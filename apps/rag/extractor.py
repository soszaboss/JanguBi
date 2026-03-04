import logging
from apps.rag.llm_client import AsyncGeminiClient
from apps.rag.schemas import GEMINI_INTENT_JSON_SCHEMA, ExtractedIntentSchema

logger = logging.getLogger(__name__)

class IntentExtractor:
    """
    Given a user query, this class asks the LLM to structure it into intent, domains, and specific entities.
    """

    def __init__(self):
        # We use a smaller, faster model for extraction
        self.llm_client = AsyncGeminiClient(model_name="gemini-2.5-flash")
    
    async def extract(self, query: str) -> ExtractedIntentSchema:
        from datetime import date
        today = date.today().isoformat()
        prompt = (
            "You are an Intent and Entity Extractor for a Catholic Application.\n"
            f"The current date is {today}. Analyze the following user query and extract the relevant information in strict JSON format.\n"
            "Here are the rules for extraction:\n"
            "1. 'intent' must be one of: BIBLE, ROSARY, AVAILABILITY, MIXED, or UNKNOWN.\n"
            "2. 'domains' must list all the modules touched (from BIBLE, ROSARY, AVAILABILITY).\n"
            "3. If they ask about an event or date like 'today' or 'demain', convert it to a logic format or date string format YYYY-MM-DD. Calculate relative dates like 'jeudi' based on the CURRENT DATE. If they mention times like 'après 16h', extract '16:00' to time_after.\n"
            "4. For BIBLE, extract the topic or keywords.\n"
            "5. For ROSARY, extract the mystery name, day, or topic.\n"
            "6. For AVAILABILITY, extract the city, date (YYYY-MM-DD format strictly), service, or time constraints.\n\n"
            f"Query: \"{query}\""
        )
        
        try:
            result = await self.llm_client.generate_structured(prompt, GEMINI_INTENT_JSON_SCHEMA)
            
            # Basic validation fallback
            if not result or "intent" not in result:
                logger.warning(f"Failed to extract intent from query: {query}")
                return {
                    "intent": "UNKNOWN", 
                    "domains": [], 
                    "entities": {"topic": None, "date": None, "time_after": None, "city": None, "service": None}
                }
            return result
        except Exception as e:
            logger.error(f"Error during intent extraction: {e}")
            return {
                "intent": "UNKNOWN", 
                "domains": [], 
                "entities": {"topic": None, "date": None, "time_after": None, "city": None, "service": None}
            }
