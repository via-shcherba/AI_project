import os
import sys
import redis
import shutil
from datetime import datetime
from celery import shared_task
from django.conf import settings # type: ignore
from redis import ConnectionPool
from .ws_dealer import connect_chat

CURRENT_DIR = os.path.dirname(__file__)
ENGINES_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '../../', 'django_engines'))

sys.path.extend([
    os.path.abspath(os.path.join(CURRENT_DIR, '../../', 'utility')),
    os.path.abspath(os.path.join(CURRENT_DIR, '../../', 'knowledge_base')),
])
from service_methods import get_current_formatted_timestamp # type: ignore
from start_import import run # type: ignore


@shared_task(name='project.tasks.delete_old_messages')
def delete_old_messages():
    for project, port in settings.REDIS_CONNECTIONS.items():
        redis_client = connect_redis(project, port)
        delete_old_messages(project, redis_client)


@shared_task(name='project.tasks.update_knowledge_bases')
def update_knowledge_bases():
    run()
    

@shared_task(name='project.tasks.update_chat_kb')
def update_chat_kb():
    for engine_name, creds in settings.CHAT_CREDS.items():
        connect_chat(creds)
        print(f"KB is updated on {engine_name}")
        

def connect_redis(project, port):
    try:
        pool = ConnectionPool(
            host="127.0.0.1",
            port=port,
            db=0,
            decode_responses=True
        )
        return redis.StrictRedis(connection_pool=pool)
    except Exception as e:
        print(f'connect_redis -> error in {project}: {e}')

        
def delete_old_messages(project, redis_client):
    try:
        counter = 0
        cursor = '0'
        while cursor != 0:
            cursor, keys = redis_client.scan(cursor)  
            
            for key in keys:
                if redis_client.type(key) == 'list':
                    hash_keys = redis_client.lrange(key, 0, -1)
                    current_time = datetime.fromisoformat(get_current_formatted_timestamp().replace("Z", "+00:00"))  
                    for hash_key in hash_keys:
                        m_hash_key = f'message:{hash_key}'
                        message = redis_client.hgetall(m_hash_key)
                        if isinstance(message, dict):         
                            message_timestamp = message.get('timestamp', '')
                            if message_timestamp:
                                message_time = datetime.fromisoformat(message_timestamp.replace('Z', '+00:00'))
                                if (current_time - message_time).total_seconds() > settings.SESSION_LIVE:  
                                    # Delete hash
                                    redis_client.delete(m_hash_key)
                                    # Delete hash from list
                                    redis_client.lrem(key, 1, hash_key)
                                    counter += 1 
        print(f'delete_old_messages_scheduler in {project}: {counter} messages deleted within {settings.SESSION_LIVE} s')
    except Exception as e:
        print(f'delete_old_messages_scheduler -> error in {project}: {e}')