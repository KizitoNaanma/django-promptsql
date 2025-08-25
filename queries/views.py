from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import StreamingHttpResponse
from .serializers import ChatRequestSerializer
from .services import process_query, reset_memory

@api_view(["POST"])
def chat_with_llm(request):
    serializer = ChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    query = data.get("query")
    session_id = data["session_id"]
    stream = data["stream"]
    reset = data["reset"]

    if reset:
        reset_memory(session_id)
        return Response({"message": "Session reset successful"})

    if not query:
        return Response({"error": "Query is required"}, status=400)

    if stream:
        def event_stream():
            for token in process_query(query, session_id, stream=True):
                yield token
        return StreamingHttpResponse(event_stream(), content_type="text/plain")

    result = process_query(query, session_id, stream=False)
    return Response({"answer": result})
