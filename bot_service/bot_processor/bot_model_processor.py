import os
import re
import sys
import json
import asyncio

CURRENT_DIR = os.path.dirname(__file__)

sys.path.extend([
    os.path.abspath(os.path.join(CURRENT_DIR, '../', dir_name))
    for dir_name in ['google_search', 'kb_search', 'utility']
])

from bot_service_methods import extract_and_replace_help_centere_url # type: ignore
from google_search_engine import Google_SE # type: ignore
from knowledge_base_search import KnowledgeBaseSearch # type: ignore


MAIN_MODEL = 'gpt-4.1-2025-04-14'
MAIN_TEMP = 0 
ERROR_MESSAGE = 'Error occured, please try again.'

class Bot:
    
    def __init__(self, bot_init, KB_init):        
        self.bot_init = bot_init
        self.google_se = Google_SE(self.bot_init.google_cse_id, self.bot_init.google_api_key) 
        self.language_detector = bot_init.language_detector      
        self.language_translator = bot_init.language_translator
        self.kb_search = KnowledgeBaseSearch(KB_init.local_faiss)
        self.languages_by_article_id = KB_init.languages_by_article_id
        self.ban_detector = bot_init.ban_detector 
        self.need_detector = bot_init.need_detector
        
        
    async def get_need_result(self, consumers, history):
        try:
            result = await self.need_detector.get_need(history, 'gpt-4o-mini-2024-07-18', 0)
            # logging           
            consumers.log_info(result) 
            return result
        except Exception as e:
            consumers.log_error(e)
            return ''
                
        
    async def get_ban_service_result(self, consumers, request):
        try:
            result = await self.ban_detector.get_result(request, 'gpt-4o-mini-2024-07-18', 0)
            # logging           
            consumers.log_info(result) 
            return result
        except Exception as e:
            consumers.log_error(e)
            return ''
                
        
    async def get_request_language(self, consumers, request):
        try:
            language = await self.language_detector.get_language(request, 'gpt-4o-mini-2024-07-18', 0)
            # logging           
            consumers.log_info(language) 
            return language
        except Exception as e:
            consumers.log_error(e)
            return 'English'
                            
    
    async def get_knowledge_search_result(self, consumers, request, show_links):   
        try:
            knowledge_search_result = await self.kb_search.getSearchResult(request, show_links)
            # logging
            if knowledge_search_result:
                consumers.log_info(knowledge_search_result[:80])
            else:
                consumers.log_info('Nothing')
                return 'Nothing'
            return knowledge_search_result
        except Exception as e:
            consumers.log_error(e)
            return 'Nothing'
    
    
    async def get_google_search_result(self, consumers, request):
        try: 
            google_search_result = await self.google_se.getArticles(request)
            # logging
            if google_search_result:
                consumers.log_info(google_search_result[:80])
            else:
                consumers.log_info('Nothing')
                return 'Nothing'
            return google_search_result
        except Exception as e:
            consumers.log_error(e)
            return 'Nothing'
    
    
    async def translate_json(self, consumers, json_str, language):
        try:
            translation = await self.language_translator.translate_json(json_str, language, 'gpt-4o-mini-2024-07-18', 0)
            consumers.log_info('success')
            return translation
        except Exception as e:
            consumers.log_error(e)
            return ' ' 
                       
    
    async def analyze_with_main_model(self, consumers, dynamic_context, user_request, filtered_history):              
        system_instruction = self.bot_init.instructions['main_instruction']
        messages = [
            {"role": "system", "content": system_instruction + '\n\nUse this context: ' + dynamic_context},
        ]
        
        if filtered_history:
            messages.extend(filtered_history)
        messages.append({"role": "user", "content": user_request})
    
        try:
            result = await self.bot_init.gpt_api.call_gpt_async(messages, MAIN_MODEL, MAIN_TEMP)
            # logging
            if result:
                consumers.log_info(result[:80]) 
            else:
                consumers.log_info('Nothing')
            return result
        except Exception as e:
            consumers.log_error(e)
    
    
    def get_saved_translations(self, user_data):
        return user_data.get('translation_dictionary', '')
       
    
    def get_user_data(self, consumers):
        user_data = consumers.get_user_data()
        if user_data:
            return user_data
        else:
            return {}
        

    def get_filtered_history(self, consumers, history):
        try:
            filtered_history = []
            for str in history:
                if str.get('type', '') == 'message' and str.get('chat', '') == 'bot':
                    response = re.sub(r'</?b>', '', str.get('response'))
                    response = re.sub(r'<br>', '', response)
                    filtered_history.append({"role": "assistant", "content": response})
                if str.get('type', '') == 'request' and str.get('chat', '') == 'bot':
                    filtered_history.append({"role": "user", "content": str.get('request')})
            filtered_history.pop()
            return filtered_history
        except Exception as e:
            consumers.log_error(e)
            return None

        
    def update_dictionary_translations(self, consumers, user_data, request_language, translations):
        try:
            user_data.update({'request_language': request_language})          
            user_data.update({'translation_dictionary': translations})                             
            consumers.update_user_data(user_data)
        except Exception as e:
            consumers.log_error(e)
        
        
    def setup_dictionary_translations(self, consumers, translations, user_data, request_language_result, saved_request_language):
        if translations:
            self.update_dictionary_translations(consumers, user_data, request_language_result, translations)
        
        if request_language_result == saved_request_language and request_language_result != consumers.default_language:
            saved_translations = self.get_saved_translations(user_data)
            if saved_translations:
                translations = saved_translations
            else:
                translations = self.convert_dict_to_str(consumers.MESSAGES)
                self.update_dictionary_translations(consumers, user_data, request_language_result, translations)
        if request_language_result == consumers.default_language:
            translations = consumers.all_dictionaries
            self.update_dictionary_translations(consumers, user_data, request_language_result, translations)
        return translations
    

    def convert_dict_to_str(self, dict_input):
        return json.dumps(dict_input, ensure_ascii=False)
    

    async def process_thread(self, name, thread, consumers):
        results_thread = await asyncio.gather(*thread.values(), return_exceptions=True)
        results_dict_thread = {key: results_thread[i] for i, key in enumerate(thread.keys())}
        for key, result in results_dict_thread.items():
            if isinstance(result, Exception):
                consumers.log_error(f"{name} error in {key}: {result}")
                results_dict_thread[key] = None
        return results_dict_thread
            

    async def get_processed_answer(self, request, history, consumers) -> dict:      
        user_data = self.get_user_data(consumers)         
        filtered_history = self.get_filtered_history(consumers, history)       
        request_base = filtered_history[-2:]
        request_base.append({'user': request})
                
        thread_1 = {
            'get_request_language': self.get_request_language(consumers, str(request_base)),
            'get_need_detector_result': self.get_need_result(consumers, str(request_base))
        }   
        
        results_dict_thread_1 = await self.process_thread('Thread_1', thread_1, consumers)
        request_language_result = results_dict_thread_1['get_request_language']              
        need_detector_result = results_dict_thread_1['get_need_detector_result']
                    
        saved_request_language = user_data.get('request_language', '')
        
        thread_2 = {
            'get_knowledge_search_result': self.get_knowledge_search_result(consumers, need_detector_result, True),
            'get_google_search_result': self.get_google_search_result(consumers, need_detector_result),
        }       
        
        results_dict_thread_2 = await self.process_thread('Thread_2', thread_2, consumers)
        knowledge_base_search_result = results_dict_thread_2.get('get_knowledge_search_result', '')
        google_search_result = results_dict_thread_2.get('get_google_search_result', '')

        thread_3 = {}        
        if request_language_result != saved_request_language and request_language_result != consumers.default_language:
            thread_3['get_translations'] = self.translate_json(consumers, self.convert_dict_to_str(consumers.MESSAGES), request_language_result)  
                             
        knowledge_base_search_result = extract_and_replace_help_centere_url(knowledge_base_search_result, request_language_result, consumers.languages_by_article_id)             
        
        dynamic_context = 'Knowledge Base Articles [\n' + knowledge_base_search_result + ']\nInternet Articles:\n' + google_search_result   
        user_request = f"Answer the user's question in {request_language_result}: [ {request} ]"
        
        thread_3['analyze_with_main_model'] = self.analyze_with_main_model(
            consumers, 
            dynamic_context, 
            user_request,
            # use two last messages from history (question, answer) to make the model more accurate
            filtered_history[-2:]
        )
            
        results_dict_thread_3 = await self.process_thread('Thread_3', thread_3, consumers)
        answer = results_dict_thread_3.get('analyze_with_main_model', '')                           
        translations = results_dict_thread_3.get('get_translations', '')    
        translations = self.setup_dictionary_translations(consumers, translations, user_data, request_language_result, saved_request_language)   
                     
        main_result = {
            "answer": answer,
            "translations": translations
        }    
        return main_result            