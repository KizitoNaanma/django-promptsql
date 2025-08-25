from django.urls import path
from .views import chat_with_llm

urlpatterns = [
    path("chat/", chat_with_llm, name="chat-with-llm"),
]
