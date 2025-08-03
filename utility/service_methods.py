import os
import re
import random
import time
import json
import pytz # type: ignore
from datetime import datetime, timezone, timedelta
from response_processing import format_history 


def generate_uuid():
    return ''.join(
        random.choice('0123456789abcdef') if c == 'x' else
        random.choice('89ab') if c == 'y' else
        c
        for c in 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
    )
    
def get_unix_epoch_time_milliseconds():
    return int(time.time() * 1000)

def convert_str_json_to_dict(str_json):
    str_json_corrected = str_json.replace("'", "\"")
    try:
        result_dict = json.loads(str_json_corrected)
        return result_dict
    except json.JSONDecodeError as e:
        print(f"service_methods --> Error decoding JSON: {e}")
        return None
    
def get_first_character(string):
    if isinstance(string, str) and string:  
        return string[0]
    else:
        raise ValueError("Invalid data in get_first_character method")
   
def get_current_formatted_timestamp():
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def get_current_time(timezone_str):
    try:           
        timezone = pytz.timezone(timezone_str)
        utc_now = datetime.now(pytz.utc)
        local_time = utc_now.astimezone(timezone)      
        return format_time(local_time)  
    except pytz.UnknownTimeZoneError:
        return ''
    
def format_time(dt): 
    hours = dt.hour 
    minutes = dt.minute 
    period = 'PM' if hours >= 12 else 'AM' 
    formatted_hours = hours % 12 or 12   
    formatted_minutes = f'{minutes:02d}' 
    return f' • {formatted_hours}:{formatted_minutes} {period}'

def add_seconds_to_date(date_str, seconds):
    date_object = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    new_date_object = date_object + timedelta(seconds=seconds)
    return new_date_object.isoformat(timespec='microseconds').replace("+00:00", "Z")

def convert_timestamp(timestamp_str):
    dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    formatted_time = dt.strftime("%d.%m.%y %H:%M")
    return formatted_time

def get_ri_env_data(workspace: str):
    env_data_keys = [
        'PREFIX',
        'CHANNEL_ID',
        'CHANNEL_TOKEN',
        'API_TOKEN',
        'AVATAR'
    ]
    ri_env_data = {}
    env_data = {
        key: os.getenv(f'RI_{workspace}_{key}')
        for key in env_data_keys
    }
    ri_env_data[workspace] = env_data
    return {key: value for key, value in ri_env_data[workspace].items()}

def get_bot_env_data(bot_id):
    env_data_keys = [
        'OPENAI_API_KEY',
        'GOOGLE_SE_ID',
        'GOOGLE_API_KEY',
        'MAIN_KB_PATH',
        'MAIN_KB_FILE',
        'ARTICLE_LANGUAGES_FILE'
    ]
    bot_env_data = {}
    
    for bot in ['B1']:
        env_data = {f'{key}': os.getenv(f'{bot}_{key}') for key in env_data_keys}
        bot_env_data[bot] = env_data
    if bot_id in bot_env_data:
        return bot_env_data[bot_id]
    return {}

def create_previous_dialog_history(chat_history):
    #chat_history = convert_strings_to_json_list(chat_history)
    history_array = []
    chat_history.reverse()
    for str in chat_history:
        if str.get('type', '') == 'message':
            add_to_history_array(history_array, str, 'response')
        if str.get('type', '') == 'request':
            add_to_history_array(history_array, str, 'request')
    history_array.reverse()
    return prepare_history_message(history_array)

def convert_strings_to_json_list(list_strings):
    return [json.loads(item) for item in list_strings]

def add_to_history_array(history_array, str, type):
    text = str.get(type, '')
    datetime = convert_timestamp(str.get('timestamp', ''))
    if not text:
        return 
    name = str.get('name') if str.get('name', '') else 'Agent'
    text = format_history(text)
    formatted_text = f'[Server {datetime}] {name} : {text}\n\n'
    if total_chars(history_array) - len(formatted_text) <= 2970:
        history_array.append(formatted_text)

def total_chars(history_array):
    return sum(len(str) for str in history_array)

def prepare_history_message(history_array):
    message = 'Previous dialogue: \n\n'
    for str in history_array:
        message += str
    return message

def remove_br_tags(json_objects):
    try:
        def clean_dict(d):
            for key, value in d.items():
                if isinstance(value, str):
                    d[key] = value.replace('<br>', '')
                elif isinstance(value, dict):
                    clean_dict(value)
                elif isinstance(value, list):
                    clean_list(value)
            return d
        def clean_list(lst):
            for index, item in enumerate(lst):
                if isinstance(item, str):
                    lst[index] = item.replace('<br>', '')
                elif isinstance(item, dict):
                    clean_dict(item)
                elif isinstance(item, list):
                    clean_list(item)
            return lst

        for json_object in json_objects:
            if json_object:
                clean_dict(json_object)
        return json_objects
    except Exception as e:
        print(f'Error in service_methods.py->remove_br_tags: {e}')
        return {}

def filter_history(data):
    filtered_data = [item for item in data if item.get('type', '') in ['request', 'message', 'analytics']]
    first_request_index = next((i for i, item in enumerate(filtered_data) if item['type'] == 'request'), -1)
    
    if first_request_index == -1:
        return []

    output_data = []
    for item in filtered_data[first_request_index:]:
        if item['type'] == 'request':
            output_data.append(item)
        elif item['type'] == 'message' and output_data:
            output_data.append(item)   
        elif item['type'] == 'analytics':
            output_data.append(item)         
    return output_data

def extract_domain(url):
    match = re.search(r'https?://([^/]+)', url)
    if match:
        return match.group(1)
    return None

def delete_db_except_user_data(key, messages, redis_client):                                                              
    for message_json in messages:
        message = json.loads(message_json)
        if message and message.get('type', '') != 'user_data':                                                       
            redis_client.lrem(key, 1, message_json)

def get_file_modify_date(file_path):
    modify_timestamp = os.path.getmtime(file_path)
    modify_date = datetime.fromtimestamp(modify_timestamp)
    return modify_date

def is_file_up_to_date(file_path, hours):
    modify_timestamp = os.path.getmtime(file_path)
    modify_date = datetime.fromtimestamp(modify_timestamp)
    current_time = datetime.now()
    time_difference = current_time - modify_date
    return time_difference <= timedelta(hours=hours)

def is_user_authorized(auth_string):
    if auth_string is None:
        return None 
    return 'auth' in auth_string

def is_localhost(url_string):
    if url_string is None:
        return None 
    return 'localhost' in url_string

def extract_user_id(auth_string):
    match = re.search(r'(auth-[^-]+)', auth_string)
    if match:
        return match.group(1)  
    return auth_string

def extract_jurisdiction(auth_string):
    parts = auth_string.split('-')
    if len(parts) > 2:
        return parts[-1] 
    return None

def to_uppercase(word):
    if word is None:
        return None  
    return word.upper()