import logging
import os
import time

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

import mlflow

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

mlflow.set_tracking_uri("http://mlflow:5000")
try:
    mlflow.set_experiment("RAG_Retriever")
except Exception:
    pass

logger.info("📚 Initializing retriever...")
start_init = time.time()

DB_DIR = os.path.join(os.path.dirname(__file__), "../data/chroma_db")
MODEL_NAME = "intfloat/multilingual-e5-base"

logger.info(f"🤖 Loading embedding model: {MODEL_NAME}...")
model_start = time.time()
model = SentenceTransformer(MODEL_NAME)
logger.info(f"✅ Model loaded in {time.time() - model_start:.2f}s")

logger.info(f"🗄️ Connecting to ChromaDB at {DB_DIR}...")
chroma_start = time.time()
client = chromadb.PersistentClient(path=DB_DIR)
collection = client.get_or_create_collection(name="medical_chunks")
logger.info(f"✅ ChromaDB connected in {time.time() - chroma_start:.2f}s")

logger.info("📊 Loading documents for BM25...")
all_data = collection.get(include=["documents", "metadatas"])

if not all_data["documents"]:
    docs, metas, ids, bm25 = [], [], [], None
    logger.warning("⚠️ No documents found in ChromaDB!")
else:
    docs = all_data["documents"]
    metas = all_data["metadatas"]
    ids = all_data["ids"]
    tokenized_docs = [doc.lower().split() for doc in docs]
    bm25 = BM25Okapi(tokenized_docs)
    logger.info(f"✅ Loaded {len(docs)} documents for BM25")

logger.info(f"🎉 Retriever initialized in {time.time() - start_init:.2f}s")


def hybrid_search(query, k=5, bm25_weight=0.3):
    logger.info(f"🔍 Hybrid search for: '{query[:50]}...' (k={k})")
    start = time.time()
    
    if not docs:
        logger.warning("⚠️ No documents available for search")
        return []
    
    # Semantic search
    logger.info("🧠 Encoding query...")
    encode_start = time.time()
    query_embedding = model.encode([query])[0]
    logger.info(f"✅ Query encoded in {time.time() - encode_start:.2f}s")
    
    logger.info("🔍 Performing semantic search...")
    semantic_start = time.time()
    semantic_results = collection.query(
        query_embeddings=[query_embedding.tolist()], n_results=k * 2
    )
    logger.info(f"✅ Semantic search completed in {time.time() - semantic_start:.2f}s")
    
    # BM25 search
    logger.info("📊 Computing BM25 scores...")
    bm25_start = time.time()
    bm25_scores = bm25.get_scores(query.lower().split())
    bm25_top = sorted(
        range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
    )[: k * 2]
    logger.info(f"✅ BM25 completed in {time.time() - bm25_start:.2f}s")
    
    # Hybrid scoring
    logger.info("⚖️ Combining scores...")
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
    
    total_time = time.time() - start
    logger.info(f"🎉 Hybrid search completed in {total_time:.2f}s - Returned {len(results)} results")
    
    return results
