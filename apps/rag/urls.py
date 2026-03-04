from django.urls import path
from apps.rag.views import RagChatApi

app_name = "rag"

urlpatterns = [
    path("query/", RagChatApi.as_view(), name="query"),
]
