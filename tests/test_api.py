"""Integration tests for POST /qa endpoint.

These tests mock the LangGraph graph so no real API calls are made.
"""
import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)

FAKE_GRAPH_RESULT = {
    "answer": "This is a test image.",
    "page_count": 1,
    "error": None,
}

# Minimal valid 1x1 PNG bytes
PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


@patch("app.api.routes.qa_graph")
def test_valid_image_returns_200(mock_graph):
    mock_graph.invoke.return_value = FAKE_GRAPH_RESULT
    response = client.post(
        "/qa",
        data={"question": "What is in this image?"},
        files={"file": ("test.png", io.BytesIO(PNG_1X1), "image/png")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "This is a test image."
    assert body["page_count"] == 1


@patch("app.api.routes.qa_graph")
def test_empty_question_returns_422(mock_graph):
    mock_graph.invoke.return_value = {
        "answer": "",
        "page_count": 0,
        "error": "Question must not be empty",
    }
    response = client.post(
        "/qa",
        data={"question": ""},
        files={"file": ("test.png", io.BytesIO(PNG_1X1), "image/png")},
    )
    assert response.status_code == 422


def test_unsupported_file_type_returns_415():
    response = client.post(
        "/qa",
        data={"question": "What is this?"},
        files={"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    assert response.status_code == 415


def test_oversized_file_returns_413():
    big_file = b"\x00" * (21 * 1024 * 1024)
    response = client.post(
        "/qa",
        data={"question": "What is this?"},
        files={"file": ("big.png", io.BytesIO(big_file), "image/png")},
    )
    assert response.status_code == 413
