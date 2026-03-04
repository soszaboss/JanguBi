import asyncio
from asgiref.sync import async_to_sync
from django.utils.decorators import classonlymethod, method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_spectacular.utils import extend_schema
from apps.rag.serializers import RagQuerySerializer, RagResponseSerializer
from apps.rag.service import RAGService

@method_decorator(transaction.non_atomic_requests, name="dispatch")
@method_decorator(csrf_exempt, name="dispatch")
class RagChatApi(APIView):
    # Asynchronous RAG Chat endpoint.
    permission_classes = [AllowAny]
    authentication_classes = []
    
    # Needs a persistent instance so we don't recreate the client per-request although minimal overhead.
    rag_service = RAGService()

    @extend_schema(
        request=RagQuerySerializer,
        responses={200: RagResponseSerializer},
        tags=["RAG"],
        summary="Ask a question to the AI assistant using RAG (Retrieval-Augmented Generation)"
    )
    def post(self, request):
        serializer = RagQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data["query"]
        
        # DRF regular APIView does not support async methods properly, so we bridge to sync
        result = async_to_sync(self.rag_service.process_query)(query)
        
        resp_serializer = RagResponseSerializer(data=result)
        resp_serializer.is_valid(raise_exception=True)

        return Response(resp_serializer.validated_data, status=status.HTTP_200_OK)
