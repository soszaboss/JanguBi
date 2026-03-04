import logging
from typing import List, Protocol

from django.conf import settings

from apps.bible.models import Verse

logger = logging.getLogger(__name__)


class EmbedderProvider(Protocol):
    """Protocol for embedding providers."""
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        ...


class StubEmbedder:
    """A stub provider that returns zero-vectors when no real provider is configured."""
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        logger.warning(
            f"Using StubEmbedder for {len(texts)} texts. "
            "Set EMBEDDING_PROVIDER in settings to use a real model."
        )
        # Using 768 dim vector (Gemini default)
        return [[0.0] * 768 for _ in texts]


class GeminiEmbedder:
    """Uses Google Gemini API for embeddings."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", None)
        self.model = "gemini-embedding-001"
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:batchEmbedContents?key={self.api_key}"

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. Falling back to zeros.")
            return [[0.0] * 768 for _ in texts]
            
        import httpx
        import time
        from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

        # Inner function for the actual API call, decorated with tenacity
        @retry(
            wait=wait_exponential(multiplier=1, min=2, max=10),
            stop=stop_after_attempt(5),
            retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
            reraise=True
        )
        def _make_request(client, url, payload):
            response = client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            return response.json()
        
        all_embeddings = []
        # Chunk texts to avoid API limits (Gemini allows ~100 per batch)
        chunk_size = 100
        for i in range(0, len(texts), chunk_size):
            chunk = texts[i:i + chunk_size]
            requests = [
                {
                    "model": f"models/{self.model}", 
                    "content": {"parts": [{"text": txt}]},
                    "outputDimensionality": 768
                }
                for txt in chunk
            ]
            payload = {"requests": requests}
            
            # We use sync httpx client because Celery workers run synchronously
            with httpx.Client() as client:
                try:
                    data = _make_request(client, self.url, payload)
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP Error fetching Gemini embeddings: {e.response.text}")
                    raise e
                except httpx.RequestError as e:
                    logger.error(f"Network error fetching Gemini embeddings: {str(e)}")
                    raise e
                    
                for emb in data.get("embeddings", []):
                    all_embeddings.append(emb["values"])
            
            # Anti-rate-limiting pause between chunks (Stay under 15 RPM)
            if i + chunk_size < len(texts):
                time.sleep(5.0)
                
        return all_embeddings


class EmbeddingService:
    """Service to handle vector embeddings generation and storage."""

    def __init__(self, provider: EmbedderProvider = None):
        if provider:
            self.provider = provider
        else:
            # Check settings logic for provider instantiation
            provider_name = getattr(settings, "EMBEDDING_PROVIDER", "stub")
            if provider_name == "stub":
                self.provider = StubEmbedder()
            elif provider_name == "gemini":
                self.provider = GeminiEmbedder()
            else:
                self.provider = StubEmbedder()
                logger.error(f"Unknown embedding provider '{provider_name}'. Falling back to stub.")

    def compute_bulk_embeddings(self, book_id: int) -> int:
        """
        Computes formatting and embeddings for all verses in a book, and saves them.
        Returns the number of verses embedded.
        """
        verses = list(Verse.objects.filter(chapter__book_id=book_id).order_by("chapter__number", "number"))
        if not verses:
            return 0

        verses_to_update = []
        for v in verses:
            # Skip if embedding exists and is non-zero
            if v.embedding is not None and sum(abs(float(val)) for val in list(v.embedding)[:10]) > 0.001:
                continue
            verses_to_update.append(v)
            
        if not verses_to_update:
            logger.info(f"All {len(verses)} verses already have non-zero embeddings in book_id {book_id}. Skipping computation.")
            return 0

        # "Genèse 1:1 - Au commencement Dieu créa le ciel et la terre."
        texts = [f"{v.chapter.book.name} {v.chapter.number}:{v.number} - {v.text}" for v in verses_to_update]
        
        try:
            vectors = self.provider.embed_texts(texts)
            
            # Batch update in memory, then bulk_update
            for v, vec in zip(verses_to_update, vectors):
                v.embedding = vec
                
            Verse.objects.bulk_update(verses_to_update, ["embedding"], batch_size=500)
            logger.info(f"Computed embeddings for {len(verses_to_update)} verses in book_id {book_id}")
            return len(verses_to_update)
        except Exception as e:
            logger.error(f"Failed to bulk compute embeddings for book_id {book_id}: {str(e)}")
            raise

    def compute_query_embedding(self, text: str) -> List[float]:
        """Computes embedding for a single search query."""
        if not text:
            return []
        vectors = self.provider.embed_texts([text])
        return vectors[0] if vectors else []
