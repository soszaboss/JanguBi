import json
import logging
import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

class AsyncGeminiClient:
    """
    Asynchronous client for interacting with the Google Gemini API using REST.
    Does not block Django main event loop.
    """
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, model_name="gemini-2.5-flash", api_key=None):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", None)
        self.model_name = model_name
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. API calls will fail.")

    async def generate_structured(self, prompt: str, schema: dict) -> dict:
        """
        Calls Gemini forcing a JSON structured output based on the provided JSON Schema.
        """
        url = f"{self.BASE_URL}/{self.model_name}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": schema,
                "temperature": 0.0 # Strict determinism for entity extraction
            }
        }

        from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

        @retry(
            wait=wait_exponential(multiplier=1, min=2, max=10),
            stop=stop_after_attempt(5),
            retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
            reraise=True
        )
        async def _make_structured_request():
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                return response.json()

        try:
            data = await _make_structured_request()
            # Extract text response which should strictly be JSON
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
            
        except httpx.HTTPError as e:
            logger.error(f"Gemini API structured generation HTTP Error: {e}")
            return {}
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse Gemini structured output: {e}")
            return {}


    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """
        Standard free-text generation for the final RAG answer.
        """
        url = f"{self.BASE_URL}/{self.model_name}:generateContent?key={self.api_key}"
        
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [{
                "parts": [{"text": user_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.2 # Slight creativity but primarily grounded
            }
        }
        
        from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

        @retry(
            wait=wait_exponential(multiplier=1, min=2, max=10),
            stop=stop_after_attempt(5),
            retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
            reraise=True
        )
        async def _make_text_request():
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=15.0)
                response.raise_for_status()
                return response.json()

        try:
            data = await _make_text_request()
            return data["candidates"][0]["content"]["parts"][0]["text"]
            
        except httpx.HTTPError as e:
            logger.error(f"Gemini API text generation HTTP Error: {e}")
            return "Je suis désolé, je n'ai pas pu générer une réponse en raison d'une erreur de connexion."
        except KeyError as e:
            logger.error(f"Failed to parse Gemini text output: {e}")
            return "Je suis désolé, je n'ai pas pu formater la réponse."
