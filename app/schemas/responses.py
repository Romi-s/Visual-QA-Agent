from pydantic import BaseModel


class QAResponse(BaseModel):
    answer: str
    page_count: int
    model: str
