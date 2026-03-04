import pytest
import datetime
from django.utils import timezone
from apps.availability.models import Parish, Minister, ServiceType, WeeklyAvailability, BlockedSlot
from apps.availability.services import AvailabilityService

@pytest.fixture
def test_data():
    parish = Parish.objects.create(name="St. Peter", city="Rome")
    # Quick creation of minister
    from apps.users.models import BaseUser
    user = BaseUser.objects.create(email="peter@example.com")
    minister = Minister.objects.create(user=user, role=Minister.Role.PRIEST, parish=parish, first_name="Peter", last_name="Saint")
    service = ServiceType.objects.create(name="Mass", slug="mass")
    
    # Create valid weekly availability (e.g. Monday 10:00 to 12:00)
    # 0 = Monday
    WeeklyAvailability.objects.create(
        minister=minister,
        weekday=0,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(12, 0),
        service_type=service
    )
    return minister

@pytest.mark.django_db
def test_find_available_ministers_basic(test_data):
    minister = test_data
    # Determine the next Monday
    today = timezone.now().date()
    days_ahead = 0 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_monday = today + datetime.timedelta(days=days_ahead)

    # Search for available ministers around 10:30 on next Monday
    available = AvailabilityService().get_available_ministers(
        date=next_monday, service_slug="mass"
    )
    assert minister in available

@pytest.mark.django_db
def test_find_available_ministers_blocked(test_data):
    minister = test_data
    today = timezone.now().date()
    days_ahead = 0 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_monday = today + datetime.timedelta(days=days_ahead)

    # Block the slot
    BlockedSlot.objects.create(
        minister=minister,
        date=next_monday,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(13, 0),
        reason="Retreat"
    )

    available = AvailabilityService().get_available_ministers(
        date=next_monday, service_slug="mass"
    )
    assert minister not in available
