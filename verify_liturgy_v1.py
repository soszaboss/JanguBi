"""Verification script for New Liturgy Offices."""
import django
import os
import asyncio
from asgiref.sync import async_to_sync, sync_to_async

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.base")
django.setup()

from apps.liturgy.services import AelfService
from apps.liturgy.models import LiturgicalDate, Office

async def verify():
    date_str = "2026-03-20"
    zone = "romain"
    
    print(f"--- Syncing data for {date_str} ---")
    await AelfService.sync_daily_data(date_str, zone)
    
    print("--- Checking Offices in DB ---")
    ld = await sync_to_async(lambda: LiturgicalDate.objects.get(date=date_str, zone=zone))()
    offices = await sync_to_async(lambda: list(Office.objects.filter(liturgical_date=ld)))()
    
    for o in offices:
        print(f"  Found Office: {o.office_type}")
        
    expected = ["laudes", "tierce", "sexte", "none", "vepres", "complies", "lectures"]
    found = [o.office_type for o in offices]
    
    missing = [e for e in expected if e not in found]
    if missing:
        print(f"!!! MISSING OFFICES: {missing}")
    else:
        print("Success: All offices found!")

if __name__ == "__main__":
    asyncio.run(verify())
