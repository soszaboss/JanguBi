from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.common.models import BaseModel


class Parish(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, db_index=True)
    country = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Paroisse"
        verbose_name_plural = "Paroisses"

    def __str__(self):
        return f"{self.name} ({self.city})"


class Minister(BaseModel):
    class Role(models.TextChoices):
        PRIEST = "PRIEST", "Priest"
        SISTER = "SISTER", "Sister"
        DEACON = "DEACON", "Deacon"
        RELIGIOUS = "RELIGIOUS", "Religious"
        BISHOP = "BISHOP", "Bishop"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="minister_profile"
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    photo = models.ImageField(upload_to="ministers/", null=True, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PRIEST)
    parish = models.ForeignKey(Parish, on_delete=models.CASCADE, related_name="ministers")
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Ministre"
        verbose_name_plural = "Ministres"
        indexes = [
            models.Index(fields=["role", "parish"]),
        ]

    def __str__(self):
        return f"{self.get_role_display()} {self.first_name} {self.last_name}"


class ServiceType(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Type de Service"
        verbose_name_plural = "Types de Service"

    def __str__(self):
        return f"{self.name} ({self.duration_minutes}m)"


class WeeklyAvailability(BaseModel):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    minister = models.ForeignKey(Minister, on_delete=models.CASCADE, related_name="weekly_availabilities")
    weekday = models.IntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name="weekly_availabilities")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Disponibilité Hebdomadaire"
        verbose_name_plural = "Disponibilités Hebdomadaires"
        constraints = [
            models.CheckConstraint(
                condition=Q(start_time__lt=F("end_time")),
                name="weekly_start_time_before_end_time"
            ),
            models.UniqueConstraint(
                fields=["minister", "weekday", "start_time", "end_time", "service_type"],
                name="unique_weekly_availability"
            )
        ]
        indexes = [
            models.Index(fields=["minister", "weekday"]),
        ]

    def __str__(self):
        return f"{self.minister} on {self.get_weekday_display()} ({self.start_time} - {self.end_time})"


class SpecialAvailability(BaseModel):
    minister = models.ForeignKey(Minister, on_delete=models.CASCADE, related_name="special_availabilities")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name="special_availabilities")

    class Meta:
        verbose_name = "Disponibilité Spéciale"
        verbose_name_plural = "Disponibilités Spéciales"
        constraints = [
            models.CheckConstraint(
                condition=Q(start_time__lt=F("end_time")),
                name="special_start_time_before_end_time"
            )
        ]
        indexes = [
            models.Index(fields=["minister", "date"]),
        ]

    def __str__(self):
        return f"{self.minister} on {self.date} ({self.start_time} - {self.end_time})"


class BlockedSlot(BaseModel):
    minister = models.ForeignKey(Minister, on_delete=models.CASCADE, related_name="blocked_slots")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Créneau Bloqué"
        verbose_name_plural = "Créneaux Bloqués"
        constraints = [
            models.CheckConstraint(
                condition=Q(start_time__lt=F("end_time")),
                name="blocked_start_time_before_end_time"
            )
        ]

    def __str__(self):
        return f"Blocked: {self.minister} on {self.date} ({self.start_time} - {self.end_time})"


class Booking(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    minister = models.ForeignKey(Minister, on_delete=models.CASCADE, related_name="bookings")
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name="bookings")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        constraints = [
            models.CheckConstraint(
                condition=Q(start_time__lt=F("end_time")),
                name="booking_start_time_before_end_time"
            )
        ]

    def __str__(self):
        return f"Booking ({self.get_status_display()}): {self.minister} on {self.date} at {self.start_time}"
