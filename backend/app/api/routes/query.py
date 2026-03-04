import time

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.security import get_current_user
from app.schemas.query import QueryCreate
from app.services.assistant_service import generate, generate_and_evaluate
from app.services.query_service import (
    create_query,
    delete_query,
    get_all_query,
    get_queries_by_user_id,
    get_query_by_id,
)
from app.models.query import Query
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("/assistant")
def query_root(query: QueryCreate,current_user: dict = Depends(get_current_user),db: Session = Depends(get_db),):
    try:
        from app.main import rag_errors, rag_latency, rag_pipeline_calls

        rag_pipeline_calls.inc()
        start = time.time()
        ai_response = generate(query.query_text, evaluate=True)
        rag_latency.observe(time.time() - start)
        saved = create_query(db, query.query_text, ai_response, current_user["id"])

        return {"question": query.query_text, "answer": ai_response, "db_id": saved.id}
    except Exception as e:
        from app.main import rag_errors

        rag_errors.inc()
        raise AppException(str(e))


@router.post("/assistant/evaluate")
def query_evaluate(query: QueryCreate,current_user: dict = Depends(get_current_user),db: Session = Depends(get_db),):
    try:
        from app.main import (
            rag_answer_relevance,
            rag_errors,
            rag_faithfulness,
            rag_latency,
            rag_pipeline_calls,
        )

        rag_pipeline_calls.inc()
        start = time.time()
        answer, metrics = generate_and_evaluate(query.query_text, k=5)
        rag_latency.observe(time.time() - start)
        saved = create_query(db, query.query_text, answer, current_user["id"])

        if metrics:
            if "answer_relevance" in metrics:
                rag_answer_relevance.set(metrics["answer_relevance"])
            if "faithfulness" in metrics:
                rag_faithfulness.set(metrics["faithfulness"])

        return {
            "question": query.query_text,
            "answer": answer,
            "metrics": metrics,
            "db_id": saved.id,
        }
    except Exception as e:
        from app.main import rag_errors

        rag_errors.inc()
        raise AppException(str(e))


@router.get("/queries")
def get_queries(current_user: dict = Depends(get_current_user),db: Session = Depends(get_db),):
    return get_all_query(db)


@router.get("/queries/{query_id}")
def get_query(query_id: int,current_user: dict = Depends(get_current_user),db: Session = Depends(get_db),):
    return get_query_by_id(db, query_id)


@router.delete("/queries/{query_id}")
def delete_query_by_id(query_id: int,current_user: dict = Depends(get_current_user),db: Session = Depends(get_db),):
    return delete_query(db, query_id)


@router.get("/queries/user/{user_id}")
def get_user_queries(user_id: int,current_user: dict = Depends(get_current_user),db: Session = Depends(get_db),):
    return get_queries_by_user_id(db, user_id)





