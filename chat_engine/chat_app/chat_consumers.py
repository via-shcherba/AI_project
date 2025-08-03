import os
import sys
import json
import time
import logging
import asyncio
import inspect
from collections import OrderedDict
from dotenv import load_dotenv  # type: ignore
from django.conf import settings # type: ignore

sys.path.extend([
    os.path.abspath(os.path.join(os.path.dirname(__file__), f'../../bot_service/bot_processor')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utility')),
])

from bot_model_static_init import Bot_Static_Init # type: ignore
from help_KB_init import Help_KB_Init # type: ignore
from bot_model_processor import Bot # type: ignore

from .consumers_helper import *
from .redis_client import redis_client 
from .dictionaries import ALL_DICTIONARIES
from channels.generic.websocket import AsyncWebsocketConsumer # type: ignore
from service_methods import * # type: ignore
from response_processing import format_response # type: ignore
from message_methods import join_bot, showTypingIndicator, send_system_message # type: ignore
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_project.settings')
load_dotenv()


class ChatConsumer(AsyncWebsocketConsumer):
        
    logger = logging.getLogger('custom_logger')
    BOT_STATIC_INIT = Bot_Static_Init()
    # Helps KB
    HELP_KB_INIT = Help_KB_Init(settings.VECTOR_STORAGE_FOLDER_PATH, settings.VECTOR_STORAGE_FILE, settings.ARTICLE_LANGUAGES_PATH)
    LOADED_BOT_MODEL_BY_CHAT_ID = OrderedDict()
    ACTIVE_CHATS = []
            
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_dictionaries = ALL_DICTIONARIES  
        self.request_queue = asyncio.Queue()
        self.languages_by_article_id = None
        self.default_language = 'English'
        self.redis_client = redis_client               
        self.bot_init_task = None
        self.request_uuid = None
        self.settings = settings
        self.bot_model = None      
        self.room_name = None
        self.time_zone = None
        self.MESSAGES = {}
        self.user_data = {}   
                                        
    
    async def connect(self):  
        try:    
            commands = []
            self.room_name = self.scope["url_route"]["kwargs"]["session_id"]            
            
            if self.room_name == 'update-kb-admin': 
                ChatConsumer.HELP_KB_INIT = Help_KB_Init(settings.VECTOR_STORAGE_FOLDER_PATH, settings.VECTOR_STORAGE_FILE, settings.ARTICLE_LANGUAGES_PATH)
                ChatConsumer.LOADED_BOT_MODEL_BY_CHAT_ID = OrderedDict()

            print(f'CONNECT {self.room_name}')    
            # Show active users amount
            ChatConsumer.ACTIVE_CHATS.append(self.room_name)
            print('ACTIVE USERS: ' + str(len(set(ChatConsumer.ACTIVE_CHATS))))
                                 
            await self.accept()
            await self.send(text_data=json.dumps([{'type' : 'connection_established'}]))

            # User Data from Redis
            user_data = self.get_user_data()    
            translation_dictionary = None      
            if user_data.get('translation_dictionary') and user_data.get('translation_dictionary') != 'null':                                         
                translation_dictionary = user_data.get('translation_dictionary')
                self.MESSAGES = convert_to_dict(self, user_data.get('translation_dictionary'))
            else:
                translation_dictionary = self.all_dictionaries
                self.MESSAGES = convert_to_dict(self, self.all_dictionaries)
                
            commands.append({'type': 'translation_dictionary', 'system_messages': translation_dictionary})  

            # Show or hide the top menu on the chat widget
            if settings.IS_TOP_MENU_SHOWN:
                commands.append({'type' : 'command', 'message': 'show_top_menu'})
            
            # Setup bot info    
            bot_info = self.get_bot_info()
            commands.append({'type': 'chat_type', 'message': 'bot', 'respondent': bot_info})

            # Get chat history from Redis                
            redis_history = self.get_chat_history()                           
            if len(redis_history) > 1:
                commands.extend(redis_history)
            else: 
                commands.append({'type' : 'empty_story'}) 
                
            commands.append({'type' : 'command', 'message': 'control'})
            await self.send(text_data=json.dumps(commands))                  
            # logging
            self.log_info(f"#connect#") 
        except Exception as e:  
            self.log_error(e)

                 
    async def disconnect(self, code):
        try:
            print(f'DISCONNECT {self.room_name}')

            if self.bot_init_task:
                self.bot_init_task.cancel()
                       
            ChatConsumer.ACTIVE_CHATS.remove(self.room_name)             
              
            # Show active users amount
            print('ACTIVE USERS: ' + str(len(set(ChatConsumer.ACTIVE_CHATS))))
            # logging
            self.log_info(f"#disconnect#")
        except Exception as e:
            self.log_error(e)
            

    async def receive(self, text_data):
        '''Processing requests from websocket'''
        try:           
            text_data_dict = convert_to_dict(self, text_data)
            # Getting user data from the client                         
            if text_data_dict.get('type') == 'user_data':                                                                        
                text_data_dict.update({'user_id': self.room_name})
                self.update_user_data(text_data_dict)
                self.time_zone = text_data_dict.get('time_zone') if text_data_dict.get('time_zone', '') else None                
                # Logging
                self.log_info(f'#user_data# {text_data_dict}')                               
                # Bot model initializing
                self.bot_model = ChatConsumer.LOADED_BOT_MODEL_BY_CHAT_ID.get(self.room_name, None)
                if self.bot_model is None:
                    self.bot_init_task = asyncio.create_task(self.initialize_bot())
            # Ping Pong with the client
            elif text_data_dict.get('type') == 'ping':
                await self.send(text_data=json.dumps([{'type' : 'pong'}]))
            elif text_data_dict.get('type') == 'connection_date':
                self.save_to_redis(text_data_dict)
                await self.join_bot(text_data_dict, True)
            elif text_data_dict.get('type') == 'grade':              
                setAnswerGrade(self, text_data_dict)                        
            elif text_data_dict.get('type') == 'request': 
                self.request_uuid = text_data_dict.get('uuid', '')    
                text_data_dict.update({'chat': 'bot'})
                self.save_to_redis(text_data_dict)                                                                                  
                await self.send_message_to_bot(text_data_dict)
            # System commands
            elif text_data_dict.get('type') == 'command': 
                if text_data_dict.get('message') == 'stop':   
                    await self.close()
                # For authorization
                elif text_data_dict.get('message') == 'restart_backend': 
                    await self.send(text_data=json.dumps([{'type': 'command', 'message': 'restart_frontend'}]))                  
                # USED IN WIDGET MENU
                elif text_data_dict.get('message') == 'clear_chat':
                    ChatConsumer.LOADED_BOT_MODEL_BY_CHAT_ID = OrderedDict()
                    delete_redis_data_by_user_id(self, self.room_name)
                    await self.close()                                                                                                                                      
        except json.JSONDecodeError as e:
            self.log_error(f'JSONException: {e} Request: {text_data}')
        except Exception as e:
            self.log_error(f'Exception: {e} Request: {text_data} Converted request: {text_data_dict}')
                         
    
    async def initialize_bot(self):
        try:
            if self.bot_model is None:  
                self.bot_model = Bot(self.BOT_STATIC_INIT, ChatConsumer.HELP_KB_INIT)
                self.languages_by_article_id = ChatConsumer.HELP_KB_INIT.languages_by_article_id 
                
                ChatConsumer.LOADED_BOT_MODEL_BY_CHAT_ID[self.room_name] = self.bot_model 
                if len(ChatConsumer.LOADED_BOT_MODEL_BY_CHAT_ID) > settings.MAX_BOT_MODELS_LOADED:
                    ChatConsumer.LOADED_BOT_MODEL_BY_CHAT_ID.popitem(last=False)     
                print(f'***BOT MODELS LOADED: {str(len(ChatConsumer.LOADED_BOT_MODEL_BY_CHAT_ID))}')
        except Exception as e:
            self.log_error(e)      


    async def send_message_to_bot(self, text_data_dict):
        print('***Request for Bot***')
        try:
            request = text_data_dict.get('request', '')
            if request:
                self.log_info(f"{request[:40]}")
            bot_info = self.get_bot_info()
            response = await self.ask_bot(request, bot_info)

            if isinstance(response, list) and len(response) > 0:
                response = response[0]
            elif not isinstance(response, dict):
                self.log_error(f"Unexpected response type: {type(response)}")
                return          
            answer = response.get('answer', '')
            
            translations = response.get('translations', '')
            self.MESSAGES = convert_to_dict(self, translations)
            await self.setup_ui_translation(translations)
            
            formatted_answer = format_response(answer)       
            disclaimer = self.MESSAGES.get('DISKLAIMER_MSG', '') if len(formatted_answer) >= settings.LEN_DISCLAIMER else ''

            response_dict = {
                'type': 'message',
                'chat': 'bot',
                'name': bot_info.get('name', ''),
                'avatar': bot_info.get('avatar', ''),
                'response': formatted_answer,
                'like': str(True),
                'disclaimer': disclaimer,
                'for_message_uuid': text_data_dict.get('uuid', ''),
                'scroll': text_data_dict.get('scroll', str(False)),
                'uuid': generate_uuid(),
                'user_time': get_current_time(self.time_zone), # type: ignore
            }
            
            if response:
                await self.send(text_data=json.dumps([response_dict]))
                self.save_to_redis(response_dict)
        except Exception as e:
            self.log_error(f'Error: {e}. Request: {text_data_dict}')         


    async def setup_ui_translation(self, translations):
        '''Translation of titles on widget (names, titles, buttons)'''
        if translations:
            await self.send(text_data=json.dumps([{'type' : 'translation_dictionary', 'system_messages': translations}])) 
                                                                
        
    def get_bot_info(self):
        return {
            'name': self.MESSAGES.get('BOT_NAME', 'Bot'),
            'avatar': settings.BOT_AVATAR,
            'greetings': self.MESSAGES.get('BOT_GREETING', ''),
            'response': self.MESSAGES.get('BOT_FIRST_RESPONSE', '')
        }
        
        
    async def join_bot(self, text_data_dict, is_unread=False):
        try:
            user_time = text_data_dict.get('user_time')
            bot_info = self.get_bot_info()
            await join_bot(self, bot_info, user_time, is_unread) 
            self.log_info('#bot_joined#')
        except Exception as e:
            self.log_error(e)


    async def ask_bot(self, request, bot_info):
        try:
            await self.request_queue.put(request)
            return await self.process_request_queue(bot_info)
        except Exception as e:
            self.log_error(e)
            return {}  


    async def process_request_queue(self, bot_info):
        responses = []
        while not self.request_queue.empty():
            request = await self.request_queue.get()
            await showTypingIndicator(self, bot_info)
            response = await self._process_single_request(request)
            responses.append(response)
            print('***Response from Bot***')
            self.request_queue.task_done()
        return responses
    

    async def _process_single_request(self, request):
        try:
            history = self.get_chat_history()            
            return await self.bot_model.get_processed_answer(request, history, self)              
        except Exception as e:
            self.log_error(e)
            await send_system_message(self, self.MESSAGES.get('CONNECTION_ERROR_MSG', ''), get_current_time(self.time_zone)) # type: ignore
            return {}  
                                                                        
        
    def extract_history_for_bot(self):
        return extract_history_for_bot(self)


    def log_info(self, info, json_body=None):
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        caller_method = caller_frame.f_code.co_name
        caller_class = caller_frame.f_locals.get('self', None).__class__.__name__
        extra = {'chat_id': self.room_name} 
        log_message = 'None'
        if info:
            log_message = info        
        if self.request_uuid:
            extra.update({'request_id': self.request_uuid})
        if json_body:
            extra.update({'json_body': json_body}) 
        self.logger.info(f"{caller_class}-->{caller_method}: {log_message}", extra=extra)                    


    def log_error(self, error):
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        caller_method = caller_frame.f_code.co_name
        caller_class = caller_frame.f_locals.get('self', None).__class__.__name__
        self.logger.error(f"{caller_class}-->{caller_method}: {error}", extra={'chat_id': self.room_name, 'request_id': self.request_uuid})
                                      
    
    def update_redis_user_data_field(self, field, value):
        update_redis_user_data_field(self, self.room_name, field, value)
                    
    
    def update_user_data(self, user_data):
        save_redis_user_data(self, self.room_name, user_data)
        
        
    def get_user_data(self):
        return get_redis_user_data(self, self.room_name)
    
    
    def get_chat_history(self):
        return get_redis_history(self, self.room_name)
                
        
    def save_to_redis(self, message_dict):
        save_message_to_redis(self, self.room_name, message_dict)