from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_async_session
from database.initialization import add_embedding, init_db
from database.manager import db_manager
from logger.config import setup_logging
from services.query_handler import query_handler
from utils.schemas import AskRequest, AskResponse, HistoryItemSchema


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    """Set up the application lifespan management."""
    setup_logging()
    await init_db()
    await add_embedding()

    yield

app = FastAPI(
    version="1.0.0",
    title="AI Knowledge Assistant",
    description="An intelligent assistant that answers user questions "
                "based on internal knowledge and contextual embeddings.",
    lifespan=lifespan,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
async def serve_frontend() -> FileResponse:
    """Serve the frontend application by returning the main HTML file from the static directory.

    This function is an endpoint for the root URL of the application and serves the
    `index.html` file located in the `static` directory. It handles asynchronous
    requests and serves as the entry point for the client-side application.
    """
    return FileResponse(Path("static") / "index.html")

@app.post("/api/ask", response_model=AskResponse)
async def ask_endpoint(
    payload: AskRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> AskResponse:
    """Represent the API endpoint to handle 'ask' requests.

    It processes a user's question, retrieves relevant context based on text embeddings, and returns
    a generated answer. The function integrates with an asynchronous session context
    and uses pre-defined models and utility functions for embedding retrieval and
    answer generation.
    """
    question = payload.question.strip()
    contexts = await query_handler.get_relevant_contexts(question, session, top_n=1)

    if not contexts:
        return AskResponse(answer="Sorry, I don't have enough information to answer that question.")

    answer = await query_handler.generate_answer(question, contexts)
    await db_manager.create_history_item(item=HistoryItemSchema(question=question, answer=answer), session=session)
    return AskResponse(answer=answer)

@app.get("/api/history", response_model=list[HistoryItemSchema])
async def get_history(session: Annotated[AsyncSession, Depends(get_async_session)]) -> list[HistoryItemSchema]:
    """Retrieve history items from the database.

    This function fetches a list of history items from the database using the
    provided async database session. It is designed to work within a FastAPI
    application and returns the data in the specified response schema.
    """
    return await db_manager.read_history_items(session=session)
