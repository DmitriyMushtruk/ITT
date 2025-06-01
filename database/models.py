from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class FAQ(Base):
    """Represent an FAQ entry in the database.

    This class defines the structure of an FAQ entry table in the database, including
    the attributes that represent the table's columns. It can be used to store and
    retrieve frequently asked questions, along with their associated metadata.
    """

    __tablename__ = "faq_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String, index=True)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)


class QAHistory(Base):
    """Represent the history of question-and-answer entries.

    This class is used to store a record of questions and their corresponding answers,
    along with a timestamp of when the record was created. It is typically part of
    a database schema for tracking or auditing Q&A interactions.
    """

    __tablename__ = "qa_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(String, nullable=False)
    answer: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(tz=ZoneInfo("Europe/Warsaw")),
        nullable=False,
    )
