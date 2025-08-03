from . import chat_consumers
from django.urls import re_path
from django.conf import settings


websocket_urlpatterns = []

if settings.IS_LOCAL_RUN:
    websocket_urlpatterns.append(re_path(r"ws/chat/(?P<session_id>[\w-]+)/", chat_consumers.ChatConsumer.as_asgi()))
else:
    websocket_urlpatterns.append(re_path(r"wss/chat/(?P<session_id>[\w-]+)/", chat_consumers.ChatConsumer.as_asgi()))