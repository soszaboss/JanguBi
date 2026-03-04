from django.contrib import admin
from apps.availability.models import (
    Parish,
    Minister,
    ServiceType,
    WeeklyAvailability,
    SpecialAvailability,
    BlockedSlot,
    Booking,
)

@admin.register(Parish)
class ParishAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "is_active")
    search_fields = ("name", "city")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("is_active", "city")


@admin.register(Minister)
class MinisterAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "role", "parish", "is_active")
    search_fields = ("first_name", "last_name", "slug")
    prepopulated_fields = {"slug": ("first_name", "last_name")}
    list_filter = ("role", "is_active", "parish")


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_minutes", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("is_active",)


@admin.register(WeeklyAvailability)
class WeeklyAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("minister", "weekday", "start_time", "end_time", "service_type", "is_active")
    list_filter = ("weekday", "is_active", "minister", "service_type")
    search_fields = ("minister__first_name", "minister__last_name")


@admin.register(SpecialAvailability)
class SpecialAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("minister", "date", "start_time", "end_time", "service_type")
    list_filter = ("date", "minister", "service_type")
    search_fields = ("minister__first_name", "minister__last_name")


@admin.register(BlockedSlot)
class BlockedSlotAdmin(admin.ModelAdmin):
    list_display = ("minister", "date", "start_time", "end_time", "reason")
    list_filter = ("date", "minister")
    search_fields = ("minister__first_name", "minister__last_name", "reason")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("minister", "service_type", "date", "start_time", "end_time", "status")
    list_filter = ("status", "date", "minister", "service_type")
    search_fields = ("minister__first_name", "minister__last_name")
