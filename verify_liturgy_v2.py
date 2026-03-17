"""Verification script for New Liturgy Offices with content check."""
import django
import os
import asyncio
from asgiref.sync import sync_to_async

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.base")
django.setup()

from apps.liturgy.services import AelfService
from apps.liturgy.models import LiturgicalDate, Office

async def verify():
    date_str = "2026-03-20"
    zone = "afrique"
    
    print(f"--- Syncing data for {date_str} (Zone: {zone}) ---")
    await AelfService.sync_daily_data(date_str, zone)
    
    print("--- Checking Offices in DB ---")
    ld = await sync_to_async(lambda: LiturgicalDate.objects.get(date=date_str, zone=zone))()
    offices = await sync_to_async(lambda: list(Office.objects.filter(liturgical_date=ld)))()
    
    for o in offices:
        content_summary = f"Hymn: {len(o.hymn)} chars, Psalms: {len(o.psalms)}, Canticle: {len(o.canticle)} chars"
        print(f"  Office: {o.office_type.ljust(10)} | {content_summary}")
        
    expected = ["laudes", "tierce", "sexte", "none", "vepres", "complies", "lectures"]
    found = [o.office_type for o in offices]
    
    missing = [e for e in expected if e not in found]
    if missing:
        print(f"!!! MISSING OFFICES: {missing}")
    
    # Specific check for Sexte (the user mentioned it was empty)
    sexte = next((o for o in offices if o.office_type == "sexte"), None)
    if sexte:
        if len(sexte.psalms) == 0:
            print("!!! WARNING: Sexte has NO psalms!")
        if len(sexte.hymn) == 0:
            print("!!! WARNING: Sexte has NO hymn!")
            
    print("\nVerification complete.")

if __name__ == "__main__":
    asyncio.run(verify())
