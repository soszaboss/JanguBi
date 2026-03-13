from django.contrib import admin

from apps.tv.models import Category, Video


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    search_fields = ("name", "slug")
    list_filter = ("order",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_live", "is_pinned_live", "created_at")
    search_fields = ("title", "youtube_url", "category__name")
    list_filter = ("category", "is_live", "is_pinned_live")
    autocomplete_fields = ("category",)
    ordering = ("-is_pinned_live", "-is_live", "-created_at")
