from typing import List, Optional, TypedDict


class QAState(TypedDict):
    file_bytes: bytes
    file_mime: str
    question: str
    images: List[bytes]
    page_count: int
    answer: str
    error: Optional[str]
