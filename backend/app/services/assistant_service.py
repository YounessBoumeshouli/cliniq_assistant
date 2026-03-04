import os

import ollama
from app.rag.retriever import hybrid_search
from app.services.evaluator import evaluate

import mlflow

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
    chunks = hybrid_search(question, k) or []
    retrieval_context = [c.get("content", "") for c in chunks]
    context = "\n\n---\n\n".join(retrieval_context)

    client = ollama.Client(host=OLLAMA_HOST)
    full_prompt = SYSTEM_PROMPT.format(context=context, question=question)

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

    answer = response["message"]["content"].replace("\n", " ")
    return answer


def generate_and_evaluate(question: str, k: int = 5):
    with mlflow.start_run(run_name="rag_pipeline"):

        mlflow.log_params(LLM_CONFIG)
        mlflow.log_param("k", k)

        chunks = hybrid_search(question, k) or []
        answer = generate(question, k=k)

        metrics = evaluate(question, answer, chunks, k=k)

        return answer, metrics
