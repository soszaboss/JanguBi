import logging
import datetime
from django.utils import timezone
from asgiref.sync import sync_to_async
from apps.availability.services import AvailabilityService
from apps.rag.schemas import EntitiesSchema

logger = logging.getLogger(__name__)

class AvailabilityEngine:
    """
    RAG Engine for retrieving priest/sister availability.
    Strictly NO vector search; queries SQL securely via AvailabilityService.
    """

    @sync_to_async
    def get_slots(self, entities: EntitiesSchema) -> str:
        """
        Uses explicit logic to find valid schedules based on the extracted LLM entities.
        Returns a formatted text string as context.
        """
        date_str = entities.get("date")
        time_after = entities.get("time_after")
        city = entities.get("city")
        service_id = None # if service was a string, we'd need to match ID. For now skipping strict service.

        # Fallback to today if no date provided but intent explicitly targeted availability
        try:
            target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else timezone.now().date()
        except ValueError:
            target_date = timezone.now().date()

        try:
            # We fetch all ministers if no city parameter, otherwise we'd need a city filter.
            # Assuming find_available_ministers natively supports date & time logic.
            # Our `AvailabilityService` exposes `find_available_ministers(date, time, service_id)`
            
            # We need a fallback if LLM doesn't extract service exactly correctly
            service_slug = entities.get("service") or "confession"
            
            # The service expects date and service_slug
            available_ministers = AvailabilityService().get_available_ministers(
                date=target_date,
                service_slug=service_slug
            )

            if not available_ministers:
                return f"Aucun ministre (prêtre/sœur) n'est disponible le {target_date.strftime('%d/%m/%Y')}."

            contexts = [f"=== DISPONIBILITÉS {service_slug.upper()} POUR LE {target_date.strftime('%d/%m/%Y')} ==="]
            for minister in available_ministers:
                roles = minister.get_role_display()
                # Basic context output
                name = f"{minister.first_name} {minister.last_name}"
                line = f"{roles} {name}"
                if minister.parish:
                    line += f" (à {minister.parish.name}, {minister.parish.city})"
                
                # Check their availability slots for the day to give the LLM exact hours
                weekday = target_date.weekday()
                slots = minister.weekly_availabilities.filter(weekday=weekday)
                
                if slots.exists():
                    slot_times = [f"{s.start_time.strftime('%H:%M')} à {s.end_time.strftime('%H:%M')}" for s in slots]
                    line += f" -> Heures de base: {', '.join(slot_times)}"
                    
                contexts.append(line)

            return "\n".join(contexts)

        except Exception as e:
            logger.error(f"AvailabilityEngine error: {e}")
            return "Erreur lors de la vérification des disponibilités."
