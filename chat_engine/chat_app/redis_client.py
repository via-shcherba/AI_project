import redis
from dotenv import load_dotenv
from redis import ConnectionPool
from chat_project.settings import REDIS_PORT

load_dotenv()

pool = ConnectionPool(
    host='127.0.0.1',
    port=REDIS_PORT,
    db=0,
    decode_responses=True
)

redis_client = redis.StrictRedis(connection_pool=pool)

def clear_history():  
    try:
        redis_client.flushall()
        print("Redis is cleaned")
    except redis.RedisError as e:
        print(f"Error in Redis cleaning: {e}")