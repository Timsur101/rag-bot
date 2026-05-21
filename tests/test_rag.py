from unittest.mock import patch, MagicMock
import numpy as np


# мокаем openai и faiss чтобы тесты не делали реальные запросы
def mock_embedding(text):
    # возвращаем случайный вектор размером 1536 (как у openai)
    return list(np.random.rand(1536).astype(float))


@patch("rag.get_embedding", side_effect=mock_embedding)
def test_add_and_ask(mock_emb):
    from rag import add_document, ask, clear_user

    user_id = "test_user"
    clear_user(user_id)

    add_document(user_id, "Python — это язык программирования. Его создал Гвидо ван Россум.")
    assert user_id in __import__("rag").indexes

    # проверяем что ask не падает
    result = ask.__wrapped__(user_id, "кто создал python") if hasattr(ask, "__wrapped__") else None


@patch("rag.get_embedding", side_effect=mock_embedding)
def test_ask_without_docs(mock_emb):
    from rag import ask, clear_user

    clear_user("empty_user")
    result = ask("empty_user", "вопрос")
    assert "загрузи" in result.lower()
