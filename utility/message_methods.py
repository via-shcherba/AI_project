import json


async def join_bot(consumers_obj, bot_info, join_time, is_unread):   
    await join(consumers_obj, bot_info, None, join_time)  
    await send_greetings(consumers_obj, bot_info)
    await send_message(consumers_obj, bot_info, None, join_time, is_unread)
            
      
async def join(consumers_obj, sender, message_uuid, join_time):
    message = {
        'type': 'join',
        'name': sender.get('name', 'Support Agent'),
        'avatar': sender.get('avatar', ''),
        'message': consumers_obj.MESSAGES.get('JOINED_MSG', ''),
        'user_time': join_time,
        'user_id': consumers_obj.room_name     
    }
    if message_uuid:
        message.update({'uuid': message_uuid})
    await consumers_obj.send(text_data=json.dumps([message])) 
    consumers_obj.save_to_redis(message)
    
    
async def end_conversation(consumers_obj):
    message = {
        'type': 'command',
        'message': 'stop'
    }
    await consumers_obj.send(text_data=json.dumps([message]))
    consumers_obj.save_to_redis(message)
        
    
async def showTypingIndicator(consumers_obj, sender):
    message = {
        'type': 'command',
        'message': 'show_typing_indicator',
        'name': sender.get('name', ''),
        'avatar': sender.get('avatar', ''),
        'scroll': sender.get('scroll', False),
        'user_id': consumers_obj.room_name
    }
    await consumers_obj.send(text_data=json.dumps([message]))
    
    
async def hideTypingIndicator(consumers_obj):
    message = {
        'type': 'command',
        'message': 'hide_typing_indicator',
        'user_id': consumers_obj.room_name
    }
    await consumers_obj.send(text_data=json.dumps([message]))
    
    
async def show_top_spinner(consumers_obj, message_uuid, text):
    message = {
        'type': 'command',
        'message': 'show_top_spinner',
        'text': text,
        'uuid': message_uuid
    }
    await consumers_obj.send(text_data=json.dumps([message]))
    consumers_obj.save_to_redis(message)
    
    
async def hide_top_spinner(consumers_obj):
    message = {
        'type': 'command',
        'message': 'hide_top_spinner'
    }
    await consumers_obj.send(text_data=json.dumps([message]))
    consumers_obj.save_to_redis(message)
    

async def send_greetings(consumers_obj, sender):
    message = {
        'type': 'greetings',
        'greetings': sender.get('greetings', None),
        'user_id': consumers_obj.room_name
    }
    await consumers_obj.send(text_data=json.dumps([message]))
    consumers_obj.save_to_redis(message)
        

async def send_message(consumers_obj, sender, message_uuid, join_time, is_unread=False):
    message = {
        'type': 'message',
        'name': sender.get('name', ''),
        'avatar': sender.get('avatar', ''),
        'response': sender.get('response', None),
        'like': str(False),
        'scroll': str(True),
        'user_time': join_time,
        'is_unread': str(is_unread)
    }
    if message_uuid:
        message.update({'uuid': message_uuid})
    await consumers_obj.send(text_data=json.dumps([message]))
    consumers_obj.save_to_redis(message)
    
    
async def stop_file_spinner(consumers_obj, id, sent_time):
    message = {
        'type': 'command',
        'message': 'hide_file_spinner',
        'id': id,
        'sent_time': sent_time
    }
    await consumers_obj.send(text_data=json.dumps([message]))
        
    
async def send_system_message(self, message, send_time):
    text_data_dict = {
        'type' : 'system_message',
        'message': message,
        'user_time': send_time
    }
    await self.send(text_data=json.dumps([text_data_dict]))
    self.save_to_redis(text_data_dict)