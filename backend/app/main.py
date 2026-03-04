from app.api.routes import auth, query, users
from app.core.database import Base, engine
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    global_exception_handler,
)
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

rag_pipeline_calls = Counter("rag_pipeline_calls_total", "Total RAG pipeline calls")
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint"]
)
rag_latency = Histogram(
    "rag_latency_seconds",
    "RAG pipeline response latency in seconds",
    buckets=[0.5, 1, 2, 5, 10, 30, 60, 120],
)
rag_errors = Counter("rag_errors_total", "Total RAG pipeline errors")
rag_answer_relevance = Gauge("rag_answer_relevance", "Last RAG answer relevance score")
rag_faithfulness = Gauge("rag_faithfulness", "Last RAG faithfulness score")

app = FastAPI(title="CliniQ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def track_requests(request: Request, call_next):
    response = await call_next(request)
    if request.url.path != "/metrics":
        http_requests_total.labels(method=request.method, endpoint=request.url.path).inc()
    return response


app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(query.router)
app.include_router(users.router)


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def root():
    return {"message": "CliniQ API"}
