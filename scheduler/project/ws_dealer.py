import ssl
import asyncio
import websockets 
    

async def call_websocket(uri):
    ssl_context = None
    if uri.startswith('wss://'):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    try:
        async with websockets.connect(uri, ssl=ssl_context):
            await asyncio.sleep(1)
    except Exception as e:
        print(f'Connection Error: {e}')
            
            
def get_ws_url(chat_data):
    #url = f"wss://{chat_data['chat_url']}/wss/{chat_data['type']}/{chat_data['admin_id']}/"
    url = f"ws://{chat_data['chat_url']}/ws/{chat_data['type']}/{chat_data['admin_id']}/"
    return url


def connect_chat(chat_data):
    websocket_url = get_ws_url(chat_data)
    asyncio.run(call_websocket(websocket_url))