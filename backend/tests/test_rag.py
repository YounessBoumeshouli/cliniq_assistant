# ── Test 1 : Simulated retriever ───────────────────────────────────────────────


def test_retriever_simulated():
    """Simulates hybrid_search returning ChromaDB-style chunks."""

    def fake_hybrid_search(query, k=5):
        return [
            {"id": "chunk_1", "content": f"Info médicale pour: {query}", "score": 0.9},
            {"id": "chunk_2", "content": "Rincer à l'eau de mer", "score": 0.7},
        ]

    results = fake_hybrid_search("piqûre de méduse", k=2)

    assert isinstance(results, list)
    assert len(results) == 2
    for chunk in results:
        assert "content" in chunk and len(chunk["content"]) > 0
        assert "score" in chunk and 0.0 <= chunk["score"] <= 1.0


# ── Test 2 : Simulated LLM response ───────────────────────────────────────────


def test_llama3_simulated():
    """Simulates llama3 returning a response."""

    def fake_llm_chat(prompt):
        return {
            "message": {"content": "Rincer à l'eau de mer et consulter un médecin."}
        }

    response = fake_llm_chat("Que faire en cas de piqûre de méduse ?")

    assert "message" in response
    assert len(response["message"]["content"]) > 0
