import os
from django.conf import settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_project.settings')

ALL_DICTIONARIES = f'''{{
    "BOT_NAME": "{settings.BOT_NAME}",
    "BOT_GREETING": "Hi 👋, I'm {settings.BOT_NAME}, a multilingual digital assistant.",
    "BOT_FIRST_RESPONSE": "How can I help you today?",
    "CONNECTION_ERROR_MSG": "Oops! I just took a quick break — let's try that again in a moment.",
    "TYPE_Y_MSG": "Enter your message...",
    "HOW_ELSE_I_CAN_HELP_MSG": "How else I can help you?",
    "WAIT_MSG": "Wait please...",
    "LOADING_MSG": "Loading...",
    "JOINED_MSG": "joined",
    "TODAY_MSG": "Today",
    "SENT_MSG": "Sent",
    "LEFT_MSG": "left",
    "CHAT_MSG": "Chat",
    "LIKE_MSG": "Helpful",
    "DISLIKE_MSG": "Not helpful",
    "TYPING_MSG": "is typing...",
    "TRY_AGAIN": "Try again.",
    "CLOSE_MSG": "Close",
    "YES_MSG": "Yes",
    "NO_MSG": "No",
    "DISKLAIMER_MSG": "This content is for informational purposes only and not intended to be investing advice."
}}'''