from django.urls import path
from apps.rosary.views import (
    GroupListApi,
    GroupDetailApi,
    TodayRosaryApi,
    RosaryWeekdayApi,
    PrayerListApi,
    MysteryDetailApi,
    RosarySearchApi,
    RosaryVectorSearchApi
)

app_name = "rosary"

urlpatterns = [
    # Groups
    path("groups/", GroupListApi.as_view(), name="group-list"),
    path("groups/<slug:slug>/", GroupDetailApi.as_view(), name="group-detail"),
    
    # Days
    path("today/", TodayRosaryApi.as_view(), name="today-rosary"),
    path("day/<int:day>/", RosaryWeekdayApi.as_view(), name="day-rosary"),
    
    # Core Components
    path("prayers/", PrayerListApi.as_view(), name="prayer-list"),
    path("mysteries/<int:pk>/", MysteryDetailApi.as_view(), name="mystery-detail"),
    
    # Search
    path("search/", RosarySearchApi.as_view(), name="search"),
    #path("vector_search/", RosaryVectorSearchApi.as_view(), name="vector-search"),
]
