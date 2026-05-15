import pytest

from app.agent.nodes import convert_to_images, format_response, validate_input


def _base_state(**overrides):
    state = {
        "file_bytes": b"fake",
        "file_mime": "image/png",
        "question": "What is this?",
        "images": [],
        "page_count": 0,
        "answer": "",
        "error": None,
    }
    state.update(overrides)
    return state


def test_validate_rejects_unsupported_mime():
    result = validate_input(_base_state(file_mime="text/plain"))
    assert result["error"].startswith("Unsupported")


def test_validate_rejects_empty_question():
    result = validate_input(_base_state(question="   "))
    assert result["error"] == "Question must not be empty"


def test_validate_rejects_long_question():
    result = validate_input(_base_state(question="x" * 2001))
    assert "2000" in result["error"]


def test_validate_passes_valid_input():
    result = validate_input(_base_state())
    assert result == {}


def test_convert_wraps_image_in_list():
    state = _base_state(file_bytes=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    result = convert_to_images(state)
    assert result["page_count"] == 1
    assert len(result["images"]) == 1


def test_convert_skips_on_error():
    state = _base_state(error="prior error")
    result = convert_to_images(state)
    assert result == {}


def test_format_strips_whitespace():
    state = _base_state(answer="  hello world  ")
    result = format_response(state)
    assert result["answer"] == "hello world"


def test_format_skips_on_error():
    state = _base_state(error="some error", answer="  text  ")
    result = format_response(state)
    assert result == {}
