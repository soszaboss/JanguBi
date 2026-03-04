from rest_framework import serializers

class RagQuerySerializer(serializers.Serializer):
    query = serializers.CharField(
        required=True,
        help_text="The question or prompt to ask the assistant (e.g., 'Quel mystère aujourd'hui et as-tu un prêtre dispo à Mbour ?')"
    )

class RagResponseSerializer(serializers.Serializer):
    answer = serializers.CharField(help_text="The generated response from the LLM.")
    context = serializers.CharField(help_text="The raw context retrieved from the database.")
    intent = serializers.DictField(help_text="The metadata showing how the LLM routed the question.")
