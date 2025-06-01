import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import QAHistory
from utils.schemas import HistoryItemSchema

logger = logging.getLogger(__name__)

class DBManager:
    """A class for managing database operations."""

    @staticmethod
    async def read_history_items(*, session: AsyncSession) -> list[HistoryItemSchema]:
        """Read all history items from the database."""
        try:
            result = await session.execute(select(QAHistory).order_by(QAHistory.created_at.desc()))
            history_items = result.scalars().all()
        except SQLAlchemyError:
            logger.exception("Failed to read Q&A history")
            return []
        else:
            return [
                HistoryItemSchema(
                    question=item.question,
                    answer=item.answer,
                    created_at=item.created_at,
                ) for item in history_items
            ]

    @staticmethod
    async def create_history_item(*, item: HistoryItemSchema, session: AsyncSession) -> None:
        """Create a new history item in the database."""
        record: QAHistory = QAHistory(
            question=item.question,
            answer=item.answer,
            created_at=datetime.now(tz=ZoneInfo("Europe/Warsaw")),
        )
        try:
            session.add(record)
            await session.commit()
        except SQLAlchemyError:
            logger.exception("Failed to save Q&A to history")
            await session.rollback()


db_manager = DBManager()
