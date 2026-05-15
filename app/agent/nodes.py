import base64

from app.agent.state import QAState
from app.config import settings
from app.services.pdf_converter import pdf_to_images

ALLOWED_MIME = {"image/png", "image/jpeg", "image/webp", "application/pdf"}


def validate_input(state: QAState) -> dict:
    if state["file_mime"] not in ALLOWED_MIME:
        return {"error": f"Unsupported file type: {state['file_mime']}"}
    if not state["file_bytes"]:
        return {"error": "File content is empty"}
    if not state["question"].strip():
        return {"error": "Question must not be empty"}
    if len(state["question"]) > 2000:
        return {"error": "Question exceeds 2000 character limit"}
    return {}


def convert_to_images(state: QAState) -> dict:
    if state.get("error"):
        return {}
    try:
        if state["file_mime"] == "application/pdf":
            images = pdf_to_images(
                state["file_bytes"],
                max_pages=settings.max_pdf_pages,
                dpi=settings.image_render_dpi,
            )
        else:
            images = [state["file_bytes"]]
        return {"images": images, "page_count": len(images)}
    except Exception as exc:
        return {"error": f"File conversion failed: {exc}"}


def _query_anthropic(images: list, question: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.require_api_key())
    content = []
    for img_bytes in images:
        encoded = base64.standard_b64encode(img_bytes).decode("utf-8")
        content.append(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": encoded},
            }
        )
    content.append({"type": "text", "text": question})
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        messages=[{"role": "user", "content": content}],
    )
    return response.content[0].text


def _query_openai(images: list, question: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.require_api_key())
    image_blocks = [
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64.standard_b64encode(img).decode()}"
            },
        }
        for img in images
    ]
    image_blocks.append({"type": "text", "text": question})
    response = client.chat.completions.create(
        model=settings.openai_model,
        max_tokens=1024,
        messages=[{"role": "user", "content": image_blocks}],
    )
    return response.choices[0].message.content


def query_model(state: QAState) -> dict:
    if state.get("error"):
        return {}
    try:
        if settings.provider == "anthropic":
            answer = _query_anthropic(state["images"], state["question"])
        else:
            answer = _query_openai(state["images"], state["question"])
        return {"answer": answer}
    except Exception as exc:
        return {"error": f"Model API error: {exc}"}


def format_response(state: QAState) -> dict:
    if state.get("error"):
        return {}
    return {"answer": state["answer"].strip()}
