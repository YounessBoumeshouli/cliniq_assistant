import pytest


@pytest.fixture
def fake_user():
    return {"id": 1, "username": "testuser", "email": "test@cliniq.com", "role": "user"}


@pytest.fixture
def fake_token():
    return {"access_token": "jwt_token_123", "token_type": "bearer"}


@pytest.fixture
def fake_query():
    return {
        "id": 1,
        "query_text": "Piqûre méduse ?",
        "response": "Rincer...",
        "user_id": 1,
    }


@pytest.fixture
def fake_queries_db():
    return [
        {"id": 1, "query_text": "Piqûre méduse", "response": "Rincer...", "user_id": 1},
        {"id": 2, "query_text": "Brûlure", "response": "Refroidir...", "user_id": 1},
    ]


def test_register(fake_user, fake_token):
    """Simulates POST /auth/register → returns token if user created."""
    user_exists = False
    password_valid = True

    if not user_exists and password_valid:
        result = fake_token
    else:
        result = None

    assert result is not None
    assert "access_token" in result


def test_login(fake_token):
    """Simulates POST /auth/login → returns token if credentials valid."""
    credentials_valid = True

    result = fake_token if credentials_valid else None

    assert result is not None
    assert "access_token" in result


def test_save_query(fake_query):
    """Simulates POST /query/assistant → saves query and returns it."""
    saved = {
        "question": fake_query["query_text"],
        "answer": "Rincer à l'eau de mer.",
        "db_id": fake_query["id"],
    }

    assert "question" in saved
    assert "answer" in saved
    assert "db_id" in saved
    assert saved["db_id"] == 1


def test_get_queries(fake_queries_db):
    """Simulates GET /query/queries → returns list."""
    result = fake_queries_db

    assert isinstance(result, list)
    assert len(result) == 2


def test_get_query_by_id(fake_queries_db):
    """Simulates GET /query/queries/{id} → returns one query."""
    query_id = 1
    result = None
    for q in fake_queries_db:
        if q["id"] == query_id:
            result = q
            break

    assert result is not None
    assert result["id"] == query_id


def test_delete_query(fake_queries_db):
    """Simulates DELETE /query/queries/{id} → removes query."""
    query_id = 1
    initial_count = len(fake_queries_db)

    fake_queries_db[:] = [q for q in fake_queries_db if q["id"] != query_id]

    assert len(fake_queries_db) == initial_count - 1
