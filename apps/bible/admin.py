from django.contrib import admin

from apps.bible.models import Book, Chapter, DailyText, Testament, Verse


@admin.register(Testament)
class TestamentAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    ordering = ("order",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("name", "testament", "order", "verse_count")
    list_filter = ("testament",)
    search_fields = ("name", "slug")
    ordering = ("order",)


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("book", "number", "verse_count")
    list_filter = ("book__testament",)
    search_fields = ("book__name",)
    ordering = ("book__order", "number")


@admin.register(Verse)
class VerseAdmin(admin.ModelAdmin):
    list_display = ("chapter", "number", "source_file", "created_at")
    list_filter = ("source_file", "chapter__book__testament")
    search_fields = ("text",)
    raw_id_fields = ("chapter",)


@admin.register(DailyText)
class DailyTextAdmin(admin.ModelAdmin):
    list_display = ("date", "category", "title", "created_at")
    list_filter = ("category", "date")
    search_fields = ("title", "content")
