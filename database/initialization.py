import logging
from pathlib import Path

import aiofiles
from httpx import HTTPError
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import Base, async_session_maker, engine
from database.models import FAQ
from services.query_handler import query_handler

FAQ_TXT_PATH: Path = Path(__file__).parent / "seed.txt"

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Initialize the database connection and seed the FAQ table."""
    await create_tables()
    if await is_faq_table_empty():
        try:
            faqs: list[str] = await read_faq_file(file_path=FAQ_TXT_PATH)
            await seed_faq_table(faq_contents=faqs)
        except FileNotFoundError:
            logger.exception("FAQ file not found at path: %s", FAQ_TXT_PATH)
        except UnicodeDecodeError:
            logger.exception("Failed to decode the FAQ file. Please ensure it is UTF-8 encoded.")
        except SQLAlchemyError:
            logger.exception("Database error occurred while seeding FAQ table")


async def create_tables() -> None:
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def is_faq_table_empty() -> bool:
    """Check if the FAQ table is empty."""
    async with async_session_maker() as session:
        result = await session.execute(select(func.count()).select_from(FAQ))
        return result.scalar() == 0


async def read_faq_file(*, file_path: Path) -> list[str]:
    """Read and process lines from the FAQ file."""
    lines: list[str] = []
    async with aiofiles.open(file_path, encoding="utf-8") as file:
        async for raw_line in file:
            line: str = raw_line.strip()
            if line:
                lines.append(line)
    return lines


async def seed_faq_table(*, faq_contents: list[str]) -> None:
    """Seed the FAQ table with content."""
    async with async_session_maker() as session:
        faqs: list[FAQ] = [FAQ(content=line) for line in faq_contents]
        session.add_all(faqs)
        await session.commit()
    logger.info("Seeded %d FAQ entries into the database.", len(faqs))


async def add_embedding() -> None:
    """Add embeddings to FAQ entries with missing embeddings."""
    async with async_session_maker() as session:
        result = await session.execute(select(FAQ).where(FAQ.embedding.is_(None)))
        faqs_without_embeddings: list[FAQ] = list(result.scalars().all())

        if not faqs_without_embeddings:
            return

        logger.info("[Embedding] Found %d FAQ entries to process.", len(faqs_without_embeddings))
        await process_faq_embeddings(session=session, faqs_without_embeddings=faqs_without_embeddings)


async def process_faq_embeddings(*, session: AsyncSession, faqs_without_embeddings: list[FAQ]) -> None:
    """Compute and save embeddings for a list of FAQs."""
    for faq in faqs_without_embeddings:
        try:
            embedding_vector: list[float] = await query_handler.generate_embedding(faq.content)
            faq.embedding = embedding_vector
            session.add(faq)
            await session.commit()
            logger.info("[Embedding] Successfully processed FAQ id=%d", faq.id)
        except SQLAlchemyError:
            await session.rollback()
            logger.exception("[Embedding] Database error while processing FAQ id=%d", faq.id)
        except HTTPError:
            logger.exception("[Embedding] HTTP error while fetching embedding for FAQ id=%d", faq.id)
