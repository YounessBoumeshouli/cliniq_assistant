import json
import os

import mlflow

with open(
    os.path.join(os.path.dirname(__file__), "../data/test_case.json"),
    "r",
    encoding="utf-8",
) as f:
    TEST_CASES = json.load(f)

TEST_CASE_INDEX = {}
for tc in TEST_CASES:
    TEST_CASE_INDEX[tc["query"]] = tc["relevant_docs"]

STOPWORDS = {
    "le",
    "la",
    "les",
    "de",
    "du",
    "des",
    "un",
    "une",
    "et",
    "en",
    "à",
    "au",
    "ou",
    "que",
    "qui",
    "par",
    "sur",
    "il",
    "se",
    "ne",
    "si",
    "ce",
    "est",
    "sont",
    "avec",
    "dans",
    "pour",
    "pas",
    "plus",
    "l",
    "d",
    "s",
    "y",
    "on",
}


def get_keywords(text):
    words = set()
    for w in text.lower().split():
        w = w.strip(".,;:!?()\"'«»")
        if len(w) > 2 and w not in STOPWORDS:
            words.add(w)
    return words


def evaluate(question, answer, chunks, k=5):

    relevant_docs = TEST_CASE_INDEX.get(question.strip(), [])
    context = " ".join(c.get("content", "") for c in chunks)

    hits = 0
    for chunk in chunks:
        chunk_kw = get_keywords(chunk.get("content", ""))
        for rel in relevant_docs:
            if len(chunk_kw & get_keywords(rel)) >= 2:
                hits += 1
                break

    precision_at_k = round(hits / k, 4) if k > 0 else 0.0
    recall_at_k = round(hits / len(relevant_docs), 4) if len(relevant_docs) > 0 else 0.0

    q_kw = get_keywords(question)
    a_kw = get_keywords(answer)
    answer_relevance = round(len(q_kw & a_kw) / len(q_kw), 4) if len(q_kw) > 0 else 0.0

    ctx_kw = get_keywords(context)
    faithfulness = round(len(a_kw & ctx_kw) / len(a_kw), 4) if len(a_kw) > 0 else 0.0

    mlflow.log_metric("answer_relevance", answer_relevance)
    mlflow.log_metric("faithfulness", faithfulness)
    mlflow.log_metric("precision_at_k", precision_at_k)
    mlflow.log_metric("recall_at_k", recall_at_k)

    return {
        "answer_relevance": answer_relevance,
        "faithfulness": faithfulness,
        "precision_at_k": precision_at_k,
        "recall_at_k": recall_at_k,
    }
