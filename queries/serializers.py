from rest_framework import serializers

class ChatRequestSerializer(serializers.Serializer):
    query = serializers.CharField(required=False, allow_blank=True)
    session_id = serializers.CharField()
    stream = serializers.BooleanField(required=False, default=False)
    reset = serializers.BooleanField(required=False, default=False)
