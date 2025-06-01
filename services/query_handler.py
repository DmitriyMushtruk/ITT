import logging
import os

import numpy as np
import openai
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import FAQ

load_dotenv()

logger = logging.getLogger(__name__)

class OpenAIQueryHandler:
    """A class for handling queries to an OpenAI model."""

    def __init__(
            self,
            api_key: str | None = None,
            model: str | None = None,
            embedding_model: str | None = None,
    ) -> None:
        """Initialize the OpenAIQueryHandler with the necessary API key."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        self.model = model or os.getenv("OPENAI_MODEL")
        self.embedding_model = embedding_model or os.getenv("OPENAI_EMBEDDING_MODEL")

    async def generate_answer(
        self, question: str, contexts: list[str]) -> str:
        """Generate an answer to a question based on the provided contexts using an OpenAI model."""
        combined_context = "\n\n".join(contexts)
        system_prompt = (
            "You are a helpful, friendly assistant for TechShop, an online electronics store.\n"
            "When you answer, do the following:\n"
            "  1. Use ONLY the information from the context below to answer the question.\n"
            "  2. Provide a complete, easy-to-read, conversational response. You can add examples,\n"
            "     additional tips, or polite suggestions as long as they match the context.\n"
            "  3. If the context does not contain enough information, say you are sorry and that you do not know,\n"
            "     but keep a friendly tone.\n\n"
            f'Context:\n"""\n{combined_context}\n"""\n\n'
            f"User's Question:\n{question}\n\n"
            "Answer:"
        )
        logger.info("Requesting answer from OpenAI with prompt: %s", system_prompt)
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
            ],
            temperature=0.8,
            max_tokens=512,
        )
        logger.info("Received answer from OpenAI: %s", completion)
        return completion.choices[0].message.content.strip()

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding for the given text using the OpenAI embedding model."""
        response = await self.client.embeddings.create(input=text, model=self.embedding_model)
        return response.data[0].embedding

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute the cosine similarity between two vectors."""
        a_arr = np.array(a, dtype=np.float32)
        b_arr = np.array(b, dtype=np.float32)
        denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
        if denom == 0:
            return 0.0
        return float(np.dot(a_arr, b_arr) / denom)

    async def get_relevant_contexts(
        self,
        question: str,
        session: AsyncSession,
        top_n: int = 1,
        similarity_threshold: float = 0.4,
    ) -> list[str]:
        """Retrieve the most relevant contexts for a question based on cosine similarity of embeddings."""
        query_embedding: list[float] = await self.generate_embedding(question)
        result = await session.execute(select(FAQ).where(FAQ.embedding.is_not(None)))
        faqs = result.scalars().all()

        scored: list[tuple[float, FAQ]] = []
        for faq in faqs:
            if faq.embedding:
                score = self._cosine_similarity(query_embedding, faq.embedding)
                scored.append((score, faq))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_matches: list[str] = [faq.content for score, faq in scored if score >= similarity_threshold]
        return top_matches[:top_n]


query_handler = OpenAIQueryHandler()
