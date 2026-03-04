import datetime
from django.db.models import Prefetch, Q, F
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.utils import timezone
from apps.rosary.models import MysteryGroup, Mystery, Prayer, MysteryPrayer, RosaryDay

class RosaryService:
    @staticmethod
    def get_groups():
        """Returns all mystery groups."""
        return MysteryGroup.objects.all().order_by("id")

    @staticmethod
    def get_group_with_mysteries(group_id_or_slug):
        """Returns a group with its mysteries, but not necessarily all prayers."""
        qs = MysteryGroup.objects.prefetch_related(
            Prefetch("mysteries", queryset=Mystery.objects.order_by("order"))
        )
        if isinstance(group_id_or_slug, int) or str(group_id_or_slug).isdigit():
            return qs.get(id=int(group_id_or_slug))
        return qs.get(slug=group_id_or_slug)

    @staticmethod
    def get_daily_rosary(day_of_week: int = None):
        """
        Retrieves the Rosary mapping for a specific day of the week (0=Monday, 6=Sunday).
        If None is provided, defaults to today's weekday.
        """
        if day_of_week is None:
            day_of_week = timezone.now().weekday()
        
        # We need the day, group, mysteries, and their prayers (for the today endpoint)
        prefetch_prayers = Prefetch(
            "group__mysteries__prayers",
            queryset=MysteryPrayer.objects.select_related("prayer").order_by("order")
        )
        
        return RosaryDay.objects.select_related("group").prefetch_related(
            Prefetch("group__mysteries", queryset=Mystery.objects.order_by("order")),
            prefetch_prayers
        ).get(weekday=day_of_week)

    @staticmethod
    def get_today_rosary():
        """Returns today's rosary by delegating to get_daily_rosary."""
        return RosaryService.get_daily_rosary()

    @staticmethod
    def get_all_standalone_prayers():
        """Returns prayers typically used in the intro / closing, not tied to mysteries directly."""
        # Intro and closing prayers like Creed, Glory Be, Hail Holy Queen, etc.
        # Everything from Prayer, we could return all or filter by type
        return Prayer.objects.all().order_by("type", "language", "id")

    @staticmethod
    def search_text(query: str):
        """
        Full-text search on prayers. Uses the `tsv` column if it's populated.
        Since we might not have the DB triggers set up for auto-tsv population yet,
        we'll build the SearchVector dynamically or fall back to it.
        """
        search_query = SearchQuery(query, config="french")
        search_query = SearchQuery(query, config="french")
        
        return Prayer.objects.filter(tsv=search_query).annotate(
            rank=SearchRank(F("tsv"), search_query)
        ).order_by("-rank")

    @staticmethod
    def vector_search(query: str, embedding: list = None):
        """
        Placeholder/Stub for future RAG / pgvector integration.
        Currently returns an empty QuerySet of Prayers.
        """
        # When pgvector is fully enabled:
        # return Prayer.objects.filter(embedding__cosine_distance=embedding).order_by("embedding__cosine_distance")
        return Prayer.objects.none()
