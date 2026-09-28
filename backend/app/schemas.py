from pydantic import BaseModel
from typing import List, Optional

class AskRequest(BaseModel):
    query: str

class SourceEvidence(BaseModel):
    chunk_id: str
    page: int
    text: str

class AskResponse(BaseModel):
    answer: str
    sources: List[SourceEvidence]
