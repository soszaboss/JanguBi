import datetime
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.liturgy.models import LiturgicalDate, Reading, Office
from apps.liturgy.serializers import (
    LiturgicalDateSerializer,
    ReadingSerializer,
    OfficeSerializer
)


class LiturgyTodayApi(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses=LiturgicalDateSerializer, 
        tags=["Liturgy"], 
        summary="Get today's Liturgical data (Mass Readings, Offices)",
        description="""
        Retrieve the official liturgical texts for the CURRENT day (in the 'romain' zone).
        This includes the 'Mass' readings (First Reading, Gospel, etc.) and the 
        Liturgy of the Hours text blocks (Lauds, Vespers, Compline, etc.).
        """
    )
    @method_decorator(cache_page(60 * 60 * 1))
    def get(self, request):
        today = timezone.localtime().date()
        date_obj = LiturgicalDate.objects.filter(date=today, zone="romain").prefetch_related(
            "readings__matched_verses", "offices"
        ).first()

        if not date_obj:
            return Response(
                {"error": "Liturgy data for today has not been synchronized yet."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Flag for serializer caching
        date_obj._prefetched_objects_cache = date_obj._prefetched_objects_cache or {}
        date_obj._prefetched_objects_cache["readings"] = date_obj.readings.all()
        date_obj._prefetched_objects_cache["offices"] = date_obj.offices.all()

        serializer = LiturgicalDateSerializer(date_obj)
        return Response(serializer.data)


class LiturgyDateApi(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses=LiturgicalDateSerializer, 
        tags=["Liturgy"], 
        summary="Get Liturgical data for a specific date",
        description="""
        Retrieve the liturgical texts for a specific date (YYYY-MM-DD).
        If the data is not available locally, this endpoint returns a 404.
        """
    )
    def get(self, request, date_str):
        from django.core.cache import cache
        
        # 1. Vérifie le cache MANUELLEMENT pour éviter les 404 indésirables
        cache_key = f"liturgy_date_api_v1_{date_str}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        try:
            target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        date_obj = LiturgicalDate.objects.filter(date=target_date, zone="romain").prefetch_related(
            "readings__matched_verses", "offices"
        ).first()

        # 2. Si ça n'existe pas ENCORE, on ne met PAS en cache !
        if not date_obj:
            return Response(
                {"error": f"Liturgy data for {date_str} not found in database."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        date_obj._prefetched_objects_cache = date_obj._prefetched_objects_cache or {}
        date_obj._prefetched_objects_cache["readings"] = date_obj.readings.all()
        date_obj._prefetched_objects_cache["offices"] = date_obj.offices.all()

        serializer = LiturgicalDateSerializer(date_obj)
        
        # 3. Ce n'est qu'en cas de SUCCÈS 200 qu'on gèle le résultat pour 24h
        cache.set(cache_key, serializer.data, timeout=60 * 60 * 24)
        
        return Response(serializer.data)


class ReadingDetailApi(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses=ReadingSerializer, 
        tags=["Liturgy"], 
        summary="Get details of a specific Mass Reading",
        description="""
        Retrieve a specific Reading (e.g., the Gospel) by its ID.
        This includes any matched local Bible verses (cross-references).
        """
    )
    @method_decorator(cache_page(60 * 60 * 24))
    def get(self, request, pk):
        try:
            reading = Reading.objects.prefetch_related("matched_verses").get(pk=pk)
            serializer = ReadingSerializer(reading)
            return Response(serializer.data)
        except Reading.DoesNotExist:
            return Response({"error": "Reading not found."}, status=status.HTTP_404_NOT_FOUND)


class OfficeDetailApi(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses=OfficeSerializer, 
        tags=["Liturgy"], 
        summary="Get details of a specific Office (e.g., Lauds)",
        description="""
        Retrieve a specific Office by its ID. 
        Returns the hymns, psalms, and intercessions associated with that office.
        """
    )
    @method_decorator(cache_page(60 * 60 * 24))
    def get(self, request, pk):
        try:
            office = Office.objects.get(pk=pk)
            serializer = OfficeSerializer(office)
            return Response(serializer.data)
        except Office.DoesNotExist:
            return Response({"error": "Office not found."}, status=status.HTTP_404_NOT_FOUND)