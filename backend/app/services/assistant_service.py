import logging
import os
import time

import ollama
from app.rag.retriever import hybrid_search
from app.services.evaluator import evaluate

import mlflow

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

mlflow.set_tracking_uri("http://mlflow:5000")
mlflow.set_experiment("RAG_Pipeline")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")

LLM_CONFIG = {
    "model": "llama3",
    "temperature": 0.0,
    "top_p": 0.9,
    "top_k": 40,
    "num_predict": 2000,
}

SYSTEM_PROMPT = """
Tu es un assistant médical basé sur un système RAG.

RÈGLE PRINCIPALE :
Tu dois répondre uniquement si la question de l’utilisateur est liée au contexte médical fourni.

1️⃣ Si la question est un simple message (ex: "bonjour", "salut", "merci") :
→ Réponds naturellement et poliment, sans utiliser le contexte médical.

2️⃣ Si la question est liée au contexte médical fourni :
→ Commence toujours par :
"Bonjour 👋, voici ce que j’ai trouvé pour vous :"

→ Reformule les informations du contexte de manière claire, structurée et professionnelle.
→ Intègre naturellement les informations.
→ N’ajoute AUCUNE information qui ne figure pas dans le contexte.
→ Ne fais aucune supposition.
→ Ne réponds qu’avec les éléments explicitement présents dans le contexte.

3️⃣ Si la question ne correspond PAS au contexte médical fourni :
→ Réponds exactement :
"Votre question est hors du contexte médical disponible. Je ne peux pas y répondre."

6. Si l'information n'est PAS dans le contexte: "Cette information n'est pas disponible dans ma documentation."

CONTEXTE (5 documents trouvés - utilise TOUS ceux qui sont pertinents):
{context}

Question: {question}
La réponse doit être rédigée sous forme de texte fluide et naturel, comme si elle venait d’un assistant intelligent.

RÈGLE PRINCIPALE :
Tu dois répondre uniquement si la question de l’utilisateur est liée au contexte médical fourni.

1️⃣ Si la question est un simple message (ex: "bonjour", "salut", "merci") :
→ Réponds naturellement et poliment, sans utiliser le contexte médical.

2️⃣ Si la question est liée au contexte médical fourni :
→ Commence toujours par :
"Bonjour 👋, voici ce que j’ai trouvé pour vous :"

→ Reformule les informations du contexte de manière claire, structurée et professionnelle.
→ Intègre naturellement les informations.
→ N’ajoute AUCUNE information qui ne figure pas dans le contexte.
→ Ne fais aucune supposition.
→ Ne réponds qu’avec les éléments explicitement présents dans le contexte.

3️⃣ Si la question ne correspond PAS au contexte médical fourni :
→ Réponds exactement :
"Votre question est hors du contexte médical disponible. Je ne peux pas y répondre."

IMPORTANT :
Ne force jamais une réponse médicale si la question ne concerne pas le contexte."""


def generate(question: str, evaluate: bool = False, k: int = 5) -> str:
    logger.info(f"🔍 Starting generation for question: {question[:50]}...")
    start_total = time.time()
    
    # Step 1: Retrieval
    logger.info("📚 Step 1: Starting hybrid search...")
    start_retrieval = time.time()
    chunks = hybrid_search(question, k) or []
    retrieval_time = time.time() - start_retrieval
    logger.info(f"✅ Retrieval completed in {retrieval_time:.2f}s - Found {len(chunks)} chunks")
    
    retrieval_context = [c.get("content", "") for c in chunks]
    context = "\n\n---\n\n".join(retrieval_context)
    
    # Step 2: Ollama connection
    logger.info(f"🤖 Step 2: Connecting to Ollama at {OLLAMA_HOST}...")
    start_ollama_connect = time.time()
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        ollama_connect_time = time.time() - start_ollama_connect
        logger.info(f"✅ Ollama connection established in {ollama_connect_time:.2f}s")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Ollama: {e}")
        raise
    
    full_prompt = SYSTEM_PROMPT.format(context=context, question=question)
    logger.info(f"📝 Prompt length: {len(full_prompt)} characters")
    
    # Step 3: LLM generation
    logger.info(f"💭 Step 3: Generating response with model {LLM_CONFIG['model']}...")
    start_llm = time.time()
    try:
        response = client.chat(
            model=LLM_CONFIG["model"],
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant clinique strict basé sur RAG.",
                },
                {"role": "user", "content": full_prompt},
            ],
            options={
                "temperature": LLM_CONFIG["temperature"],
                "top_p": LLM_CONFIG["top_p"],
                "top_k": LLM_CONFIG["top_k"],
                "num_predict": LLM_CONFIG["num_predict"],
            },
        )
        llm_time = time.time() - start_llm
        logger.info(f"✅ LLM generation completed in {llm_time:.2f}s")
    except Exception as e:
        logger.error(f"❌ LLM generation failed: {e}")
        raise
    
    answer = response["message"]["content"].replace("\n", " ")
    
    total_time = time.time() - start_total
    logger.info(f"🎉 Total generation time: {total_time:.2f}s")
    logger.info(f"⏱️  Breakdown: Retrieval={retrieval_time:.2f}s, Ollama Connect={ollama_connect_time:.2f}s, LLM={llm_time:.2f}s")
    
    return answer


def generate_and_evaluate(question: str, k: int = 5):
    logger.info("🔬 Starting generation with evaluation...")
    start = time.time()
    
    with mlflow.start_run(run_name="rag_pipeline"):
        mlflow.log_params(LLM_CONFIG)
        mlflow.log_param("k", k)
        
        chunks = hybrid_search(question, k) or []
        answer = generate(question, k=k)
        
        logger.info("📊 Starting evaluation...")
        eval_start = time.time()
        metrics = evaluate(question, answer, chunks, k=k)
        eval_time = time.time() - eval_start
        logger.info(f"✅ Evaluation completed in {eval_time:.2f}s")
        
        total = time.time() - start
        logger.info(f"🎉 Total time with evaluation: {total:.2f}s")
        
        return answer, metrics
