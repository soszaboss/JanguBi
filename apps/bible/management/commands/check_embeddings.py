import logging
from django.core.management.base import BaseCommand
from apps.bible.models import Verse, Book
from django.db.models import Count, Q

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Displays the status of Bible verse vectorization (embeddings)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Bible Embedding Status Report"))
        self.stdout.write("=" * 40)

        total_verses = Verse.objects.count()
        
        # We count any non-null embedding as 'vectorized' for the high-level summary.
        # Note: In post-seeding, all verses have [0,0...] vectors, so they are not NULL.
        # To find 'true' embeddings, we'd need to check magnitude, but isnull is the fastest first check.
        vectorized_q = Q(embedding__isnull=False)
        vectorized_count = Verse.objects.filter(vectorized_q).count()
        
        self.stdout.write(f"Total Verses: {total_verses}")
        self.stdout.write(f"Has Vector:   {vectorized_count} ({round(vectorized_count/total_verses*100, 2) if total_verses else 0}%)")
        self.stdout.write(f"Missing:      {total_verses - vectorized_count}")
        self.stdout.write("-" * 40)

        # Breakdown by Book
        # Use child relationship path for annotation
        books_qs = Book.objects.annotate(
            total_v=Count('chapters__verses'),
            vectorized_v=Count('chapters__verses', filter=Q(chapters__verses__embedding__isnull=False))
        ).order_by('order')

        self.stdout.write(f"{'Book Name':<25} | {'Status':<15} | {'%':<5}")
        self.stdout.write("-" * 50)

        for book in books_qs:
            percentage = round(book.vectorized_v / book.total_v * 100, 1) if book.total_v else 0
            status_bar = f"{book.vectorized_v}/{book.total_v}"
            
            if book.vectorized_v == book.total_v and book.total_v > 0:
                color = self.style.SUCCESS
            elif book.vectorized_v > 0:
                color = self.style.WARNING
            else:
                color = self.style.NOTICE

            self.stdout.write(color(f"{book.name:<25} | {status_bar:<15} | {percentage:>4}%"))

        self.stdout.write("=" * 40)
        self.stdout.write(self.style.SUCCESS("Note: Status 100% means vectors are PRESENT (even if they are still zero-vectors from initial seeding)."))
        self.stdout.write(self.style.SUCCESS("Done."))
