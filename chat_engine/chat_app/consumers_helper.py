import os
import re
import sys
import json
from datetime import datetime
from django.utils.timezone import localtime # type: ignore

sys.path.extend([
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../', 'utility')),
])

from service_methods import generate_uuid, get_current_formatted_timestamp # type: ignore
from response_processing import clean_html # type: ignore


def save_message_to_redis(self, user_id, message):
    try:
        message_id = generate_uuid()
        timestamp = get_current_formatted_timestamp()
        mapping = {
            'user_id': user_id,
            'timestamp': timestamp
        }
        mapping.update(message)
        if not mapping.get('uuid'):
            mapping['uuid'] = message_id
        else:
            message_id = mapping.get('uuid')
        self.redis_client.hset(f'message:{message_id}', mapping=mapping)
        self.redis_client.rpush(user_id, message_id)
    except Exception as e:
        self.log_error(f'{e} message uuid: {message_id}')

    
def get_redis_history(self, user_id):
    '''Redis doesn't like dict in dict. To avoid this I save dict in dict as string.'''
    try:
        message_ids = self.redis_client.lrange(user_id, 0, -1) 
        messages = []
        for msg_id in message_ids:
            message = self.redis_client.hgetall(f'message:{msg_id}')
            if message.get('type') == 'file' and isinstance(message.get('response'), str):
                try:
                    message['response'] = json.loads(message['response'])
                except json.JSONDecodeError:
                    self.log_error(f"Json Decode Error ID {msg_id}: {message['response']}")
            messages.append(message)
        return messages
    except Exception as e:
        self.log_error(e)
        return []
    

def get_redis_user_data(self, user_id):
    try:
        return self.redis_client.hgetall(f'user:{user_id}')
    except Exception as e:
        self.log_error(e)
        

def update_redis_user_data_field(self, user_id, field, value):
    try:
        self.redis_client.hset(f'user:{user_id}', field, value)
    except Exception as e:
        self.log_error(e)
        
        
def save_redis_user_data(self, user_id, user_data):
    try:
        data_to_save = filter_user_data(user_data)
        filtered_data = {key: value for key, value in data_to_save.items() if value is not None}
        if filtered_data:  
            self.redis_client.hmset(f'user:{user_id}', filtered_data)
    except Exception as e:
        self.log_error(e)
        
        
def update_message_in_redis_history(self, message_id, new_message):
    try:        
        self.redis_client.hset(f'message:{message_id}', mapping=new_message)
        return True
    except Exception as e:
        self.log_error(e)
        return False
    
    
def get_message_from_redis_by_uuid(self, message_uuid):
    try:        
        message = self.redis_client.hgetall(f'message:{message_uuid}')
        if message:
            return message
        else:
            return {}
    except Exception as e:
        self.log_error(e)
        return {}
             
        
def convert_to_dict(self, str):
    try:
        return json.loads(str)
    except json.JSONDecodeError as e:
        self.log_error(e)
        return {}
    
    
def convert_to_string(self, dict_input):
    try:
        return json.dumps(dict_input, ensure_ascii=False)
    except json.JSONDecodeError as e:
        self.log_error(e)
        return ''
           

def extract_history_for_bot(self):
    try:
        result = []
        requests = {}
        all_history = get_redis_history(self, self.room_name)       
        for entry in all_history:
            entry_type = entry.get('type')           
            if entry_type == 'request':
                requests[entry['uuid']] = entry['request']
            elif entry_type == 'message' and 'for_message_uuid' in entry:
                for_uuid = entry['for_message_uuid']
                if for_uuid in requests:
                    response_cleaned = clean_html(entry['response'])
                    result.append([requests[for_uuid], response_cleaned])                   
        return result
    except Exception as e:
        self.log_error(e)
        return []


def setAnswerGrade(self, evaluation):
    evaluation_id = evaluation.get('id')
    grade = evaluation.get('grade')
    if evaluation_id and grade: 
        message = get_message_from_redis_by_uuid(self, evaluation_id)
        message.update({'grade': grade})
        update_message_in_redis_history(self, evaluation_id, message)
            
    
def delete_redis_data_by_user_id(self, user_id):
    try:
        user_key = f'user:{user_id}'
        hash_keys = self.redis_client.lrange(user_id, 0, -1)
        for hash_key in hash_keys:
            m_hash_key = f'message:{hash_key}'
            self.redis_client.delete(m_hash_key)
        self.redis_client.delete(user_key)
        self.redis_client.delete(user_id)     
        print(f'Deleted User Data for user: {user_id}')
        self.log_info('success')
    except Exception as e:
        self.log_error(e)
        
        
def filter_user_data(user_data):
    return {
        'user_id': user_data.get('user_id'),
        'request_language': user_data.get('request_language'),  
        'translation_dictionary': user_data.get('translation_dictionary'),
        'js_version': user_data.get('js_version'),
    } 