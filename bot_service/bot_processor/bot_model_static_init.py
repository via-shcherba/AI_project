import os
import sys
from dotenv import load_dotenv # type: ignore

CURRENT_DIR = os.path.dirname(__file__)

sys.path.extend([
    os.path.abspath(os.path.join(CURRENT_DIR, '../', dir_name))
    for dir_name in ['gpt_api', 'utility', 'language_detector', 'translator', 'ban_service_detector', 'need_detector']
])

from gpt import GPT_API # type: ignore
from bot_service_methods import read_files_to_dict # type: ignore
from language_detector_model import LanguageDetector # type: ignore
from language_translator_model import LanguageTranslator # type: ignore
from ban_detector_model import BanDetector # type: ignore
from need_detector_model import NeedDetector # type: ignore

INSTRUCTIONS_BASE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, 'instructions'))

INSTRUCTIONS = {
    'main_instruction': r'/main_model.txt',
    'language_detector_instruction': r'/language_detector.txt',
    'json_translator_instruction': r'/json_translator.txt',
    'text_translator_instruction': r'/text_translator.txt',
    'ban_detector_instruction': r'/ban_detector.txt',
    'need_detector_instruction': r'/need_detector.txt'
}

class Bot_Static_Init:
    
    def __init__(self):
        load_dotenv()
        self.processor_open_ai_key = os.environ.get("OPENAI_API_KEY")
        self.gpt_api = GPT_API(self.processor_open_ai_key)
        self.instructions = read_files_to_dict(INSTRUCTIONS_BASE_PATH, INSTRUCTIONS)
        self.google_cse_id = os.environ.get("GOOGLE_SE_ID")
        self.google_api_key = os.environ.get("GOOGLE_API_KEY")        
        self.language_detector = LanguageDetector(self.gpt_api, self.instructions['language_detector_instruction'])    
        self.language_translator = LanguageTranslator(self.gpt_api, self.instructions['json_translator_instruction'], self.instructions['text_translator_instruction'])
        self.ban_detector = BanDetector(self.gpt_api, self.instructions['ban_detector_instruction'])          
        self.need_detector = NeedDetector(self.gpt_api, self.instructions['need_detector_instruction'])    