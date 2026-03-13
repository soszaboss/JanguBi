from django.core.management.base import BaseCommand
from django.db import transaction

from apps.tv.models import Category


class Command(BaseCommand):
    help = "Initialize default TV categories."

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = Category.ensure_default_categories()
        self.stdout.write(self.style.SUCCESS(f"TV categories initialized. Newly created: {created_count}"))
