"""Quick diagnostic script for AELF liturgy import."""
import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.base")
django.setup()

from django_celery_results.models import TaskResult
from apps.liturgy.models import AelfDataEntry, LiturgicalDate, Reading, Office

print("=== LITURGY DB STATUS ===")
print(f"AelfDataEntry count: {AelfDataEntry.objects.count()}")
print(f"LiturgicalDate count: {LiturgicalDate.objects.count()}")
print(f"Reading count: {Reading.objects.count()}")
print(f"Office count: {Office.objects.count()}")

print("\n=== RECENT CELERY TASK RESULTS (liturgy) ===")
tasks = TaskResult.objects.filter(task_name__icontains="liturgy").order_by("-date_done")[:10]
for t in tasks:
    print(f"  Task: {t.task_name}")
    print(f"  Status: {t.status}")
    print(f"  Done: {t.date_done}")
    if t.result:
        print(f"  Result: {t.result[:200]}")
    if t.traceback:
        print(f"  Traceback: {t.traceback[:500]}")
    print("  ---")

if not tasks:
    print("  (No liturgy task results found)")

print("\n=== ALL RECENT FAILED TASKS ===")
failed = TaskResult.objects.filter(status="FAILURE").order_by("-date_done")[:5]
for t in failed:
    print(f"  Task: {t.task_name} | {t.date_done}")
    if t.traceback:
        print(f"  Traceback: {t.traceback[:500]}")
    print("  ---")

if not failed:
    print("  (No failed tasks)")
