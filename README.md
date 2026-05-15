# Visual QA Agent

A backend service that answers natural-language questions about uploaded images and PDF documents. Built with **FastAPI** for the REST API layer and **LangGraph** for orchestrating a multi-step agentic workflow that validates input, converts documents, queries a vision-language model, and formats the response.

## Key Capabilities

- **Multi-format input** -- PNG, JPEG, WebP images and multi-page PDF documents (converted to images via PyMuPDF)
- **Dual-provider VLM support** -- Anthropic Claude (claude-sonnet-4-6) and OpenAI GPT-4o, switchable by environment variable
- **Stateful agentic pipeline** -- LangGraph `StateGraph` with conditional error-abort edges so failures short-circuit cleanly
- **Production-ready API** -- file-type detection (magic bytes via `filetype`), size limits, structured Pydantic responses, global exception handler

## Architecture

```
POST /qa  (file + question)
     |
     v
 +-----------+     +-----------+     +-------------+     +--------+
 | validate  |---->| convert   |---->| query_model |---->| format |
 +-----------+     +-----------+     +-------------+     +--------+
     |  abort          |  abort           |  abort
     +---------->------+-------->---------+--------> END (error)
```

Each node is a pure function `(state) -> partial-state-update` wired through LangGraph's `StateGraph`. Conditional edges check for errors after every node and abort early if one is set.

### Project Layout

```
visual-qa-agent/
  app/
    agent/
      state.py          # QAState TypedDict (shared graph state schema)
      nodes.py          # validate_input, convert_to_images, query_model, format_response
      graph.py          # StateGraph wiring and compilation -> qa_graph
    api/
      routes.py         # POST /qa endpoint (file upload, MIME detection, graph invocation)
    schemas/
      responses.py      # QAResponse Pydantic model
    services/
      pdf_converter.py  # pdf_to_images() using PyMuPDF with configurable DPI
    config.py           # pydantic-settings config (provider, API keys, limits)
    main.py             # FastAPI app factory with global exception handler
  tests/
    test_nodes.py       # Unit tests for each graph node function
    test_api.py         # Integration tests for POST /qa (mocked graph)
  requirements.txt
  requirements-dev.txt
  .env.example
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
pip install -r requirements-dev.txt   # for tests

cp .env.example .env
# Edit .env -- set PROVIDER and the matching API key
```

## Running

```bash
uvicorn app.main:app --reload
```

The server starts at `http://127.0.0.1:8000`. Interactive docs at `/docs` (Swagger) and `/redoc`.

### Example Request

```bash
curl -X POST http://127.0.0.1:8000/qa \
  -F "file=@invoice.pdf" \
  -F "question=What is the total amount due?"
```

```json
{
  "answer": "The total amount due on the invoice is $1,250.00.",
  "page_count": 3,
  "model": "claude-sonnet-4-6"
}
```

## Testing

```bash
pytest tests/ -v
```

Unit tests cover all graph nodes (validation rules, image wrapping, error short-circuiting, whitespace stripping). Integration tests cover the HTTP layer (valid requests, MIME rejection, file-size limits) with the LangGraph graph mocked out.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `PROVIDER` | `anthropic` | `anthropic` or `openai` |
| `ANTHROPIC_API_KEY` | -- | Required when provider is anthropic |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Anthropic model identifier |
| `OPENAI_API_KEY` | -- | Required when provider is openai |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model identifier |
| `MAX_FILE_SIZE_MB` | `20` | Upload size limit |
| `MAX_PDF_PAGES` | `20` | Max PDF pages to process |
| `IMAGE_RENDER_DPI` | `150` | DPI for PDF-to-image rendering |

## Tech Stack

- **Python 3.9+**
- **FastAPI** + **Uvicorn** -- async HTTP server
- **LangGraph** (LangChain ecosystem) -- stateful agent graph orchestration
- **Anthropic SDK** / **OpenAI SDK** -- vision-language model clients
- **PyMuPDF (fitz)** -- PDF page rendering
- **Pydantic v2** + **pydantic-settings** -- data validation and env config
- **filetype** -- magic-byte MIME detection
- **pytest** + **httpx** -- testing
