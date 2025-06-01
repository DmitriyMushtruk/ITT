from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from database.manager import db_manager
from main import app
from services.query_handler import query_handler

client = TestClient(app)


@pytest.mark.asyncio
@patch("main.get_async_session", new_callable=AsyncMock)
@patch("database.manager.db_manager.create_history_item", new_callable=AsyncMock)
@patch("services.query_handler.query_handler.get_relevant_contexts", new_callable=AsyncMock)
@patch("services.query_handler.query_handler.generate_answer", new_callable=AsyncMock)
async def test_ask_endpoint_valid_request(
        mock_generate_answer,
        mock_get_relevant_contexts,
        mock_create_history_item,
        mock_get_async_session,
) -> None:
    """Test the ask endpoint with a valid request."""
    mock_get_relevant_contexts.return_value = ["relevant context"]
    mock_generate_answer.return_value = (
        "We accept credit cards (Visa, MasterCard), "
        "digital wallets (PayPal, Apple Pay), and "
        "installment plans through Klarna."
    )

    payload = {"question": "Which payment methods do you accept?"}
    response = client.post("/api/ask", json=payload)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"answer": mock_generate_answer.return_value}
    mock_get_relevant_contexts.assert_awaited_once()
    mock_generate_answer.assert_awaited_once()


@pytest.mark.asyncio
@patch("main.get_async_session", new_callable=AsyncMock)
@patch("database.manager.db_manager.create_history_item", new_callable=AsyncMock)
@patch("services.query_handler.query_handler.get_relevant_contexts", new_callable=AsyncMock)
@patch("services.query_handler.query_handler.generate_answer", new_callable=AsyncMock)
async def test_ask_endpoint_no_contexts(
        mock_generate_answer,
        mock_get_relevant_contexts,
        mock_create_history_item,
        mock_get_async_session,
) -> None:
    """Test the ask endpoint with no relevant contexts."""
    mock_get_relevant_contexts.return_value = []
    payload = {"question": "Why is the sky blue?"}
    response = client.post("/api/ask", json=payload)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"answer": "Sorry, I don't have enough information to answer that question."}
    mock_get_relevant_contexts.assert_awaited_once()
    mock_generate_answer.assert_not_awaited()


@pytest.mark.asyncio
@patch("main.get_async_session", new_callable=AsyncMock)
async def test_ask_endpoint_invalid_request(mock_get_async_session) -> None:
    """Test the ask endpoint with an invalid request."""
    payload = {"question": "Short?"}
    response = client.post("/api/ask", json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "string_too_short" in str(response.content)


@pytest.mark.asyncio
async def test_integration_ask_endpoint(monkeypatch) -> None:
    """Test the ask endpoint with a real-world scenario."""
    async def mock_get_relevant_contexts(question, session, top_n) -> list[str]:
        return ["context_1", "context_2"]

    async def mock_generate_answer(question, contexts) -> str:
        return "You can enter the promo code during checkout in the 'Apply Discount Code' field."

    async def mock_create_history_item(item, session) -> None:
        return None

    monkeypatch.setattr(query_handler, "get_relevant_contexts", mock_get_relevant_contexts)
    monkeypatch.setattr(query_handler, "generate_answer", mock_generate_answer)
    monkeypatch.setattr(db_manager, "create_history_item", mock_create_history_item)

    payload = {"question": "Where do I enter a promo code during checkout?"}
    response = client.post("/api/ask", json=payload)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "answer": "You can enter the promo code during checkout in the 'Apply Discount Code' field.",
    }
