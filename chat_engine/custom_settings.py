import os

# CUSTOM SETTINGS

# Folders
VECTOR_STORAGE_FOLDER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../', 'knowledge_base', 'freshdesk', 'data'))
# Languages
ARTICLE_LANGUAGES_PATH = os.path.abspath(os.path.join(VECTOR_STORAGE_FOLDER_PATH, 'fd_languages_by_article_ids.txt'))
# Help
VECTOR_STORAGE_FILE = r'freshdesk_vector_storage'

# For local starting (ws or wss)
IS_LOCAL_RUN = True
# Chat port
MAIN_PORT = '8004'
REDIS_PORT = '6380'

# Chat URL
CORS_ALLOWED_ORIGINS = [
    f"http://127.0.0.1:{MAIN_PORT}"  
]

# Show links
SHOW_LINKS = True
# Main menu on widget 
IS_TOP_MENU_SHOWN = True
# Keep max bot models loaded
MAX_BOT_MODELS_LOADED = 200
# Min answer length to show disclaimer
LEN_DISCLAIMER = 200

# Bot name
BOT_NAME = "Waffet"
# Bot avatar
BOT_AVATAR = '/static/images/bot_avatar.png'
 
# List blocked ips
BLOCKED_IPS = []

# ATTENTION! THIS COMMAND WILL DELETE ANY HISTORY FROM ALL CHATS!
# python manage.py clear_redis

# GET ALL HISTORY MESSAGES BY USER ID
# python manage.py get_messages_by_id <id>

# DELETE TRANSLATIONS FOR ALL USERS
# python manage.py clear_translations