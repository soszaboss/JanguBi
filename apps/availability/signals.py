from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

from apps.availability.models import Parish, Minister, ServiceType, WeeklyAvailability, SpecialAvailability, BlockedSlot, Booking

logger = logging.getLogger(__name__)

def clear_availability_cache(sender, **kwargs):
    """
    Clears the entire Django cache when an availability-related model is modified.
    This ensures that cached paginated list views and detail views are updated
    immediately after an admin action (create/update/delete).
    """
    logger.info(f"Clearing cache due to {sender.__name__} update.")
    cache.clear()

# Register the signal for all relevant availability models
for model in [Parish, Minister, ServiceType, WeeklyAvailability, SpecialAvailability, BlockedSlot, Booking]:
    post_save.connect(clear_availability_cache, sender=model)
    post_delete.connect(clear_availability_cache, sender=model)
