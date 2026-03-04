from django.urls import path
from apps.liturgy.views import (
    LiturgyTodayApi,
    LiturgyDateApi,
    ReadingDetailApi,
    OfficeDetailApi
)

app_name = "liturgy"

urlpatterns = [
    # Core Dates
    path("today/", LiturgyTodayApi.as_view(), name="today"),
    path("date/<str:date_str>/", LiturgyDateApi.as_view(), name="specific-date"),
    
    # Specific Resource Breakdown
    path("readings/<int:pk>/", ReadingDetailApi.as_view(), name="reading-detail"),
    path("offices/<int:pk>/", OfficeDetailApi.as_view(), name="office-detail"),
]