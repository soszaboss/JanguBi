"""Diagnostic script for Sexte data."""
import django
import os
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.base")
django.setup()

from apps.liturgy.models import AelfDataEntry, Office

def diagnostic():
    # Check raw entries
    entries = AelfDataEntry.objects.filter(source_endpoint__icontains="sexte").order_by("-fetched_at")[:5]
    print(f"--- Found {entries.count()} raw entries for sexte ---")
    for entry in entries:
        print(f"Entry ID: {entry.id}, Date: {entry.date}, Zone: {entry.zone}")
        print("Raw JSON summary:")
        print(json.dumps(entry.raw_json, indent=2)[:500] + "...")
        print("-" * 20)

    # Check processed offices
    offices = Office.objects.filter(office_type="sexte").order_by("-id")[:5]
    print(f"\n--- Found {offices.count()} processed offices for sexte ---")
    for o in offices:
        print(f"Office ID: {o.id}, Date: {o.liturgical_date.date}, Zone: {o.liturgical_date.zone}")
        print(f"Hymn length: {len(o.hymn)}")
        print(f"Psalms count: {len(o.psalms)}")
        print(f"Canticle length: {len(o.canticle)}")
        print("-" * 20)

if __name__ == "__main__":
    diagnostic()
