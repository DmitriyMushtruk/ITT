from datetime import datetime

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Question to be answered."""

    question: str = Field(..., min_length=10)

class AskResponse(BaseModel):
    """Answer to the question."""

    answer: str = Field(..., min_length=30)


class HistoryItemSchema(AskRequest, AskResponse):
    """Item in the history."""

    created_at: datetime | None = None
