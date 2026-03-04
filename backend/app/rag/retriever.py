import os

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

import mlflow

mlflow.set_tracking_uri("http://mlflow:5000")
try:
    mlflow.set_experiment("RAG_Retriever")
except Exception:
    pass

DB_DIR = os.path.join(os.path.dirname(__file__), "../data/chroma_db")
MODEL_NAME = "intfloat/multilingual-e5-base"

model = SentenceTransformer(MODEL_NAME)
client = chromadb.PersistentClient(path=DB_DIR)
collection = client.get_or_create_collection(name="medical_chunks")

all_data = collection.get(include=["documents", "metadatas"])

if not all_data["documents"]:
    docs, metas, ids, bm25 = [], [], [], None
else:
    docs = all_data["documents"]
    metas = all_data["metadatas"]
    ids = all_data["ids"]
    tokenized_docs = [doc.lower().split() for doc in docs]
    bm25 = BM25Okapi(tokenized_docs)


def hybrid_search(query, k=5, bm25_weight=0.3):
    if not docs:
        return []

    query_embedding = model.encode([query])[0]

    semantic_results = collection.query(
        query_embeddings=[query_embedding.tolist()], n_results=k * 2
    )

    bm25_scores = bm25.get_scores(query.lower().split())
    bm25_top = sorted(
        range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
    )[: k * 2]

    scores = {}
    for i, doc_id in enumerate(semantic_results["ids"][0]):
        scores[doc_id] = (1 - bm25_weight) * (1 - i / (k * 2))

    for rank, idx in enumerate(bm25_top):
        doc_id = ids[idx]
        if doc_id in scores:
            scores[doc_id] += bm25_weight * (1 - rank / (k * 2))
        else:
            scores[doc_id] = bm25_weight * (1 - rank / (k * 2))

    top_ids = sorted(scores, key=scores.get, reverse=True)[:k]

    results = []
    for doc_id in top_ids:
        idx = ids.index(doc_id)
        full_metadata = metas[idx].copy()
        full_metadata["id"] = doc_id
        full_metadata["score"] = scores[doc_id]

        results.append(
            {
                "id": doc_id,
                "content": docs[idx],
                "metadata": full_metadata,
                "score": scores[doc_id],
            }
        )

    return results
