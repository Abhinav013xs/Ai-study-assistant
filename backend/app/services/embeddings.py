import logging
from typing import List
import google.generativeai as genai
import openai
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingsService:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        
        # Configure Gemini if key is present
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
        
        # Configure OpenAI if key is present
        if self.openai_key:
            openai.api_key = self.openai_key

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates embedding for a single text string.
        Falls back to a mock vector if no keys are configured.
        """
        # Primary: Gemini gemini-embedding-001 (3072 dimensions)
        if self.gemini_key:
            try:
                response = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=text,
                    task_type="retrieval_document"
                )
                return response["embedding"]
            except Exception as e:
                logger.error(f"Gemini Embedding failed: {str(e)}")

        # Secondary: OpenAI text-embedding-ada-002 (1536 dimensions)
        if self.openai_key:
            try:
                response = openai.Embedding.create(
                    model="text-embedding-ada-002",
                    input=text
                )
                return response["data"][0]["embedding"]
            except Exception as e:
                logger.error(f"OpenAI Embedding failed: {str(e)}")

        # Fallback Mock Vector (3072 dimensions to match gemini-embedding-001)
        logger.warning("No embedding API keys configured. Returning mock vector.")
        return [0.01] * 3072

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a batch of text strings.
        """
        if self.gemini_key:
            try:
                response = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=texts,
                    task_type="retrieval_document"
                )
                return response["embedding"]
            except Exception as e:
                logger.error(f"Gemini batch embedding failed: {str(e)}")

        # If not batching, or on failure, generate individually
        return [self.get_embedding(text) for text in texts]

embeddings_service = EmbeddingsService()

