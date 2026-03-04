import datetime

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from drf_spectacular.utils import extend_schema

from apps.availability.models import Parish, Minister, WeeklyAvailability, ServiceType
from apps.availability.serializers import (
    ParishSerializer,
    MinisterListSerializer,
    MinisterDetailSerializer,
    WeeklyAvailabilitySerializer,
    SlotSerializer,
    MonthCalendarSerializer,
    ServiceTypeSerializer
)
from apps.availability.filters import ParishFilter, MinisterFilter
from apps.availability.permissions import IsAdminOrSelfMinisterOrReadOnly
from apps.availability.services import AvailabilityService


class ParishListApi(generics.ListCreateAPIView):
    queryset = Parish.objects.filter(is_active=True).order_by("name")
    serializer_class = ParishSerializer
    filterset_class = ParishFilter
    permission_classes = [IsAdminOrSelfMinisterOrReadOnly]

    @extend_schema(tags=["Availability"], summary="List all active parishes")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["Availability"], summary="Create a new parish")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ParishDetailApi(generics.RetrieveUpdateDestroyAPIView):
    queryset = Parish.objects.filter(is_active=True)
    serializer_class = ParishSerializer
    permission_classes = [IsAdminOrSelfMinisterOrReadOnly]
    lookup_field = "slug"

    @extend_schema(tags=["Availability"], summary="Get parish details")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["Availability"], summary="Update parish details")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(tags=["Availability"], summary="Partially update parish details")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(tags=["Availability"], summary="Delete parish")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class MinisterListApi(generics.ListCreateAPIView):
    queryset = Minister.objects.filter(is_active=True).select_related("parish").order_by("first_name", "last_name")
    serializer_class = MinisterListSerializer
    filterset_class = MinisterFilter
    permission_classes = [IsAdminOrSelfMinisterOrReadOnly]

    @extend_schema(tags=["Availability"], summary="List all active ministers")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["Availability"], summary="Create a new minister profile")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ServiceTypeListApi(generics.ListCreateAPIView):
    queryset = ServiceType.objects.filter(is_active=True).order_by("name")
    serializer_class = ServiceTypeSerializer
    permission_classes = [IsAdminOrSelfMinisterOrReadOnly]

    @extend_schema(tags=["Availability"], summary="List all active service types")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["Availability"], summary="Create a new service type")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ServiceTypeDetailApi(generics.RetrieveUpdateDestroyAPIView):
    queryset = ServiceType.objects.filter(is_active=True)
    serializer_class = ServiceTypeSerializer
    permission_classes = [IsAdminOrSelfMinisterOrReadOnly]
    lookup_field = "slug"

    @extend_schema(tags=["Availability"], summary="Get service type details")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["Availability"], summary="Update service type")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(tags=["Availability"], summary="Partially update service type")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(tags=["Availability"], summary="Delete service type")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class MinisterDetailApi(generics.RetrieveUpdateDestroyAPIView):
    queryset = Minister.objects.filter(is_active=True).select_related("parish").prefetch_related("weekly_availabilities__service_type")
    serializer_class = MinisterDetailSerializer
    permission_classes = [IsAdminOrSelfMinisterOrReadOnly]
    lookup_field = "slug"

    @extend_schema(tags=["Availability"], summary="Get minister details")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["Availability"], summary="Update minister details")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(tags=["Availability"], summary="Partially update minister details")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(tags=["Availability"], summary="Delete minister profile")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class MinisterWeeklyApi(generics.ListAPIView):
    serializer_class = WeeklyAvailabilitySerializer
    permission_classes = [IsAdminOrSelfMinisterOrReadOnly]

    def get_queryset(self):
        slug = self.kwargs["slug"]
        return WeeklyAvailability.objects.filter(minister__slug=slug, is_active=True).select_related("service_type").order_by("weekday", "start_time")

    @extend_schema(tags=["Availability"], summary="Get minister weekly availability")
    @method_decorator(cache_page(60 * 60 * 6))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MinisterAvailableSlotsApi(APIView):
    permission_classes = [IsAdminOrSelfMinisterOrReadOnly]
    
    # Input serializer inside the view 
    class InputSerializer(serializers.Serializer):
        date = serializers.DateField()

    @extend_schema(
        tags=["Availability"],
        summary="Get available slots for a minister on a specific date",
        parameters=[InputSerializer],
        responses=SlotSerializer(many=True)
    )
    def get(self, request, slug):
        input_serializer = self.InputSerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        
        target_date = input_serializer.validated_data["date"]
        
        service = AvailabilityService()
        slots = service.get_available_slots(slug, target_date)
        
        output_serializer = SlotSerializer(slots, many=True)
        return Response(output_serializer.data)


class AvailableMinistersApi(APIView):
    permission_classes = [IsAdminOrSelfMinisterOrReadOnly]
    
    class InputSerializer(serializers.Serializer):
        date = serializers.DateField()
        service = serializers.CharField(max_length=255)

    @extend_schema(
        tags=["Availability"],
        summary="Get available ministers for a specific date and service",
        parameters=[InputSerializer],
        responses=MinisterListSerializer(many=True)
    )
    def get(self, request):
        input_serializer = self.InputSerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        
        target_date = input_serializer.validated_data["date"]
        service_slug = input_serializer.validated_data["service"]
        
        service = AvailabilityService()
        ministers = service.get_available_ministers(target_date, service_slug)
        
        output_serializer = MinisterListSerializer(ministers, many=True)
        return Response(output_serializer.data)


class MinisterCalendarApi(APIView):
    permission_classes = [IsAdminOrSelfMinisterOrReadOnly]
    
    class InputSerializer(serializers.Serializer):
        month = serializers.CharField(max_length=7) # YYYY-MM
        
        def validate_month(self, value):
            try:
                datetime.datetime.strptime(value, "%Y-%m")
            except ValueError:
                raise ValidationError("Must be in format YYYY-MM")
            return value

    @extend_schema(
        tags=["Availability"],
        summary="Get a minister's availability calendar for a specific month",
        parameters=[InputSerializer],
        responses=MonthCalendarSerializer
    )
    def get(self, request, slug):
        input_serializer = self.InputSerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        
        month_str = input_serializer.validated_data["month"]
        
        service = AvailabilityService()
        calendar_data = service.compute_month_calendar(slug, month_str)
        
        output_serializer = MonthCalendarSerializer(calendar_data)
        return Response(output_serializer.data)
