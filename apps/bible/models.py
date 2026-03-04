import logging
from typing import Optional

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.utils.text import slugify
from pgvector.django import VectorField

from apps.common.models import BaseModel

logger = logging.getLogger(__name__)


class Testament(models.Model):
    """Ancien or Nouveau Testament."""

    slug = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return self.name


class Book(BaseModel):
    """A book of the Bible (e.g. Genèse, Psaumes, Matthieu)."""

    testament = models.ForeignKey(
        Testament,
        on_delete=models.PROTECT,
        related_name="books",
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    alt_names = models.JSONField(default=list, blank=True)
    order = models.IntegerField()
    verse_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Chapter(models.Model):
    """A chapter within a book."""

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="chapters",
    )
    number = models.IntegerField()
    name = models.CharField(max_length=255, blank=True, default="")
    verse_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ("book", "number")
        ordering = ["number"]

    def __str__(self) -> str:
        return f"{self.book.name} {self.number}"


class Verse(models.Model):
    """A single verse within a chapter."""

    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name="verses",
    )
    number = models.IntegerField()
    text = models.TextField()
    original_id = models.IntegerField(null=True, blank=True)
    original_position = models.IntegerField(null=True, blank=True)
    source_file = models.CharField(max_length=128, blank=True, null=True)

    # Postgres full-text search vector
    tsv = SearchVectorField(null=True)

    # pgvector embedding
    # We use 768 dimensions for Gemini Flash embeddings
    embedding = VectorField(dimensions=768, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("chapter", "number", "source_file")
        ordering = ["number"]
        indexes = [
            GinIndex(fields=["tsv"], name="idx_verse_tsv"),
        ]

    def __str__(self) -> str:
        return f"{self.chapter} : {self.number}"


class DailyText(BaseModel):
    """Daily readings fetched from the AELF API."""

    date = models.DateField(db_index=True)
    category = models.CharField(max_length=64)  # 'messe', 'heures', 'lecture'
    title = models.CharField(max_length=255, blank=True, default="")
    content = models.TextField()
    source_url = models.URLField(blank=True, null=True)

    # Cross-references to matched verses, populated by SearchService
    local_matches = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.date} — {self.category}: {self.title[:50]}"
