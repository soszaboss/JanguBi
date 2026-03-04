from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.availability.models import Parish, Minister, ServiceType, WeeklyAvailability

User = get_user_model()

class ParishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parish
        fields = ["id", "name", "slug", "address", "city", "country", "latitude", "longitude", "is_active"]
        read_only_fields = ["slug"]


class MinisterListSerializer(serializers.ModelSerializer):
    parish = ParishSerializer(read_only=True)
    parish_id = serializers.PrimaryKeyRelatedField(source="parish", queryset=Parish.objects.all(), write_only=True)
    user_id = serializers.PrimaryKeyRelatedField(source="user", queryset=User.objects.all(), write_only=True, required=False, allow_null=True, default=None)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = Minister
        fields = ["id", "first_name", "last_name", "slug", "photo", "role", "role_display", "parish", "parish_id", "user_id", "is_active"]
        read_only_fields = ["slug"]


class ServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceType
        fields = ["id", "name", "slug", "description", "duration_minutes"]
        read_only_fields = ["slug"]


class WeeklyAvailabilitySerializer(serializers.ModelSerializer):
    service_type = ServiceTypeSerializer(read_only=True)
    weekday_display = serializers.CharField(source="get_weekday_display", read_only=True)

    class Meta:
        model = WeeklyAvailability
        fields = ["id", "weekday", "weekday_display", "start_time", "end_time", "service_type"]


class MinisterDetailSerializer(serializers.ModelSerializer):
    parish = ParishSerializer(read_only=True)
    parish_id = serializers.PrimaryKeyRelatedField(source="parish", queryset=Parish.objects.all(), write_only=True)
    user_id = serializers.PrimaryKeyRelatedField(source="user", queryset=User.objects.all(), write_only=True, required=False, allow_null=True, default=None)
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    weekly_availabilities = serializers.SerializerMethodField()

    class Meta:
        model = Minister
        fields = ["id", "first_name", "last_name", "slug", "photo", "role", "role_display", "parish", "parish_id", "user_id", "bio", "is_active", "weekly_availabilities"]
        read_only_fields = ["slug"]

    def get_weekly_availabilities(self, obj):
        request = self.context.get("request")
        if request and request.query_params.get("include_availability", "").lower() == "true":
            # Assuming prefetch_related has been called in the queryset
            return WeeklyAvailabilitySerializer(obj.weekly_availabilities.all(), many=True).data
        return []


class SlotSerializer(serializers.Serializer):
    start = serializers.TimeField(format="%H:%M")
    end = serializers.TimeField(format="%H:%M")
    service = serializers.CharField()
    service_name = serializers.CharField()


class MonthCalendarSerializer(serializers.Serializer):
    available_days = serializers.ListField(child=serializers.DateField())
    full_days = serializers.ListField(child=serializers.DateField())
    partial_days = serializers.ListField(child=serializers.DateField())
