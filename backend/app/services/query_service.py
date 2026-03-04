from app.models.query import Query
from sqlalchemy.orm import Session


def create_query(db: Session, query_text: str, response: str, user_id: int):
    db_query = Query(
        query=query_text,
        response=response,
        user_id=user_id,
    )
    db.add(db_query)
    db.commit()
    db.refresh(db_query)
    return db_query


def delete_query(db: Session, query_id: int):
    query = db.query(Query).filter(Query.id == query_id).first()
    if not query:
        return {"error": "Query not found"}
    db.delete(query)
    db.commit()
    return {"message": "Query deleted successfully"}


def get_query_by_id(db: Session, query_id: int):
    return db.query(Query).filter(Query.id == query_id).first()


def get_all_query(db: Session):
    return db.query(Query).all()


def get_queries_by_user_id(db: Session, user_id: int):
    return db.query(Query).filter(Query.user_id == user_id).all()
