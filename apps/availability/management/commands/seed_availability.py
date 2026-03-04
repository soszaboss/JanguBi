from datetime import time, date, timedelta
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.availability.models import (
    Parish, Minister, ServiceType, WeeklyAvailability,
    SpecialAvailability, BlockedSlot, Booking
)

class Command(BaseCommand):
    help = "Seeds the database with dummy data for the availability app."

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting to seed the availability database...")

        # 1. Create Parishes
        parishes_data = [
            {"name": "Paroisse Saint Jean-Baptiste", "city": "Dakar", "address": "Quartier Plateau"},
            {"name": "Paroisse Marie Mère de Dieu", "city": "Abidjan", "address": "Cocody"},
            {"name": "Paroisse Saint Pierre", "city": "Paris", "address": "Montrouge"},
        ]
        
        parishes = []
        for p_data in parishes_data:
            parish, created = Parish.objects.get_or_create(
                slug=slugify(p_data["name"]),
                defaults=p_data
            )
            parishes.append(parish)
            if created:
                self.stdout.write(f"  Created Parish: {parish.name}")

        # 2. Create Service Types
        services_data = [
            {"name": "Confession", "duration_minutes": 15, "description": "Sacrement de la réconciliation"},
            {"name": "Accompagnement Spirituel", "duration_minutes": 45, "description": "Entretien et direction spirituelle"},
            {"name": "Préparation au Mariage", "duration_minutes": 60, "description": "Rencontre avec les fiancés"},
            {"name": "Bénédiction de maison", "duration_minutes": 30, "description": "Visite et bénédiction"},
        ]
        
        services = []
        for s_data in services_data:
            service, created = ServiceType.objects.get_or_create(
                slug=slugify(s_data["name"]),
                defaults=s_data
            )
            services.append(service)
            if created:
                self.stdout.write(f"  Created ServiceType: {service.name}")

        # 3. Create Ministers
        ministers_data = [
            {"first_name": "Jean-Paul", "last_name": "Koffi", "role": Minister.Role.PRIEST, "parish": parishes[0]},
            {"first_name": "Marie-Hélène", "last_name": "Sarr", "role": Minister.Role.SISTER, "parish": parishes[0]},
            {"first_name": "Pierre", "last_name": "Dubois", "role": Minister.Role.PRIEST, "parish": parishes[1]},
        ]
        
        ministers = []
        for m_data in ministers_data:
            slug = slugify(f"{m_data['first_name']} {m_data['last_name']}")
            minister, created = Minister.objects.get_or_create(
                slug=slug,
                defaults=m_data
            )
            ministers.append(minister)
            if created:
                self.stdout.write(f"  Created Minister: {minister.first_name} {minister.last_name}")

        # 4. Create Weekly Availabilities
        for minister in ministers:
            # Let's give each minister some availability on Tuesday and Thursday afternoons
            for weekday in [WeeklyAvailability.Weekday.TUESDAY, WeeklyAvailability.Weekday.THURSDAY]:
                WeeklyAvailability.objects.get_or_create(
                    minister=minister,
                    weekday=weekday,
                    start_time=time(14, 0),
                    end_time=time(17, 0),
                    service_type=services[0] # Confession
                )
            
            # Wednesday morning for Spiritual Accompaniment
            WeeklyAvailability.objects.get_or_create(
                minister=minister,
                weekday=WeeklyAvailability.Weekday.WEDNESDAY,
                start_time=time(9, 0),
                end_time=time(12, 0),
                service_type=services[1] # Accompagnement
            )
        self.stdout.write("  Created Weekly Availabilities.")

        # 5. Create some Blocked Slots (e.g. tomorrow afternoon)
        tomorrow = date.today() + timedelta(days=1)
        for minister in ministers:
            BlockedSlot.objects.get_or_create(
                minister=minister,
                date=tomorrow,
                start_time=time(14, 0),
                end_time=time(18, 0),
                reason="Retraite spirituelle ou réunion"
            )
        self.stdout.write("  Created Blocked Slots.")

        self.stdout.write(self.style.SUCCESS("Successfully seeded the availability database!"))
