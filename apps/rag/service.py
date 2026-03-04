import logging
from typing import TypedDict, Optional
from django.conf import settings

from apps.rag.extractor import IntentExtractor
from apps.rag.router import QueryRouter
from apps.rag.context_builder import ContextBuilder
from apps.rag.llm_client import AsyncGeminiClient

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# 1. Extraction du prompt hors de la logique métier
# ----------------------------------------------------------------------------
RAG_SYSTEM_PROMPT_TEMPLATE = """Tu es un assistant IA Catholique précis, factuel et respectueux.
Tu dois répondre STRICTEMENT à partir du CONTEXTE fourni.

RÈGLES ABSOLUES :
- N'utilise AUCUNE connaissance externe.
- Ne reformule PAS les versets : cite-les exactement tels qu'ils apparaissent.
- Si une information n'est pas présente dans le contexte, réponds : 'Je ne trouve pas cette information dans le contexte fourni.'
- Ne complète jamais un verset partiel.
- Ne déduis aucune information implicite.
- Ne produis aucune interprétation théologique non présente dans le contexte.
- Si plusieurs thèmes sont demandés, structure clairement la réponse en sections.

Réponds de manière claire, structurée et concise.

CONTEXTE :
{context}
"""

# ----------------------------------------------------------------------------
# 2. Typage robuste du retour (Clean Code)
# ----------------------------------------------------------------------------
class RAGResponse(TypedDict):
    answer: str
    context: str
    intent: dict

class RAGService:
    """
    The orchestrator that runs the entire RAG pipeline from a raw user string to the final LLM response.
    """

    # 3. Injection de dépendances pour faciliter le Mocking et les tests
    def __init__(
        self, 
        extractor: Optional[IntentExtractor] = None,
        router: Optional[QueryRouter] = None,
        context_builder: Optional[ContextBuilder] = None,
        final_llm: Optional[AsyncGeminiClient] = None
    ):
        self.extractor = extractor or IntentExtractor()
        self.router = router or QueryRouter()
        self.context_builder = context_builder or ContextBuilder()
        
        # Le nom du modèle devient dynamique
        model_name = getattr(settings, 'GEMINI_MODEL_NAME', 'gemini-2.5-flash')
        self.final_llm = final_llm or AsyncGeminiClient(model_name=model_name)

    async def process_query(self, query: str) -> RAGResponse:
        """
        Executes the async RAG flow: Extract -> Route/Retrieve -> Build Context -> Final LLM
        """
        # 4. Validation des entrées (Sécurité)
        if not query or not query.strip():
            return RAGResponse(answer="La requête est vide.", context="", intent={})
            
        if len(query) > 1000:  # Limite de sécurité arbitraire (ex. 1000 chars utiles)
            return RAGResponse(
                answer="Votre question est trop longue, veuillez la raccourcir.",
                context="",
                intent={}
            )

        # Troncature pour des logs propres et sans risque PII massif
        logger.info(f"RAG processing query: {query[:100]}...")

        intent_data = {}
        
        # 5. Gestion native des erreurs et pannes potentielles d'API ou de BD
        try:
            # Étape 1 : Extract
            intent_data = await self.extractor.extract(query)
            logger.info(f"Extracted Intent: {intent_data}")

            # Fallback out of scope
            if intent_data.get("intent") == "UNKNOWN" and not intent_data.get("domains"):
                return RAGResponse(
                    answer="Désolé, je suis uniquement formé pour répondre aux questions concernant la Bible, le Rosaire et les disponibilités des prêtres/sœurs. Pouvez-vous reformuler votre question ?",
                    context="",
                    intent=intent_data
                )

            # Étape 2 : Route & Retrieve
            engine_results = await self.router.route_to_engines(intent_data)

            # Étape 3 : Build Context
            context_string = self.context_builder.build(engine_results)

            # 6. Économie de tokens (Performance) : Ne pas appeler le LLM vide
            if not context_string or not context_string.strip():
                return RAGResponse(
                    answer="Je ne trouve malheureusement pas cette information dans mes documents de référence actuels.",
                    context="",
                    intent=intent_data
                )

            # Étape 4 : Final Generation Context
            system_prompt = RAG_SYSTEM_PROMPT_TEMPLATE.format(context=context_string)

            final_answer = await self.final_llm.generate_text(
                system_prompt=system_prompt,
                user_prompt=query
            )

            return RAGResponse(
                answer=final_answer,
                context=context_string,
                intent=intent_data
            )
        except Exception as e:
            # Catcher toutes les erreurs de timeout/réseau pour éviter une page 500 violente
            logger.error(f"Error processing RAG pipeline for query '{query[:50]}': {e}", exc_info=True)
            return RAGResponse(
                answer="Désolé, une erreur interne empêche de traiter votre question pour le moment. Veuillez réessayer plus tard.",
                context="",
                intent=intent_data
            )
