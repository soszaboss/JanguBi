from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.db.models import F, Q
from apps.common.models import BaseModel

# Import removed since we fallback to JSON like the Bible module


from apps.rosary.storage import RosaryAudioStorage


class MysteryGroup(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    audio_file = models.FileField(storage=RosaryAudioStorage(), upload_to="", null=True, blank=True)

    def __str__(self):
        return self.name


class Mystery(BaseModel):
    group = models.ForeignKey(MysteryGroup, on_delete=models.CASCADE, related_name="mysteries")
    order = models.PositiveSmallIntegerField()  # 1 to 5
    title = models.CharField(max_length=255)
    meditation = models.TextField(null=True, blank=True, help_text="Scripture reading or meditation for the mystery")
    audio_file = models.FileField(storage=RosaryAudioStorage(), upload_to="", null=True, blank=True)
    audio_duration = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in seconds")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["group", "order"], name="unique_mystery_order_per_group")
        ]
        verbose_name_plural = "Mysteries"

    def __str__(self):
        return f"{self.group.name} - {self.order} - {self.title}"


class Prayer(BaseModel):
    class Type(models.TextChoices):
        SIGN_OF_CROSS = "SIGN_OF_CROSS", "Sign of Cross"
        CREED = "CREED", "Apostles Creed"
        OUR_FATHER = "OUR_FATHER", "Our Father"
        HAIL_MARY = "HAIL_MARY", "Hail Mary"
        GLORY_BE = "GLORY_BE", "Glory Be"
        FATIMA = "FATIMA", "Fatima Prayer"
        HOLY_QUEEN = "HOLY_QUEEN", "Hail Holy Queen"
        FINAL_PRAYER = "FINAL_PRAYER", "Final Prayer"
        OTHER = "OTHER", "Other"

    type = models.CharField(max_length=50, choices=Type.choices)
    text = models.TextField()
    language = models.CharField(max_length=10, default="FR")
    
    # Text Search Field (populated via triggers/SQL)
    tsv = SearchVectorField(null=True, blank=True)
    
    # Vector DB Search Field for Future RAG (Stubbed as JSONField for now)
    embedding = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["type"]),
        ]

    def __str__(self):
        return f"{self.get_type_display()} ({self.language})"


class MysteryPrayer(models.Model):
    mystery = models.ForeignKey(Mystery, on_delete=models.CASCADE, related_name="prayers")
    prayer = models.ForeignKey(Prayer, on_delete=models.CASCADE, related_name="mysteries")
    order = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["mystery", "order"], name="unique_prayer_order_per_mystery")
        ]
        ordering = ["order"]

    def __str__(self):
        return f"{self.mystery.title} -> {self.prayer.type} (Order: {self.order})"


class RosaryDay(BaseModel):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    weekday = models.IntegerField(choices=Weekday.choices, unique=True)
    group = models.ForeignKey(MysteryGroup, on_delete=models.CASCADE, related_name="days")

    def __str__(self):
        return f"{self.get_weekday_display()} -> {self.group.name}"
