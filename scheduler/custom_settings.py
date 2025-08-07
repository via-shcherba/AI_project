# Where shcheduler is run
MAIN_PORT = '7002'

# History older than session live will be deleted
SESSION_LIVE = 24 * 60 * 60

# Clearing histories on REDIS ports
REDIS_CONNECTIONS = {
    'chat_engine': '6380'
}
# Chat engine where copy logs
LOG_CHAT_ENGINE_NAME = 'chat_engine'
# Chat creds to update KBs
CHAT_CREDS = {
    'chat_engine': {
        'admin_id': 'update-kb-admin', 
        'type': 'chat',
        'chat_url': '127.0.0.1:8004'
    }
}  