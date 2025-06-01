from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL: str = "sqlite+aiosqlite:///./faq.db"

engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    """Base class that combines functionalities of `AsyncAttrs` and `DeclarativeBase`.

    This class is intended to serve as a foundational class for database models or
    other entities in applications requiring asynchronous attribute handling and
    SQLAlchemy ORM support. It provides essential mechanisms and
    base configurations for derived classes.
    """

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a new asynchronous session for database operations."""
    async with async_session_maker() as session:
        yield session
