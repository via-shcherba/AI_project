import os
import re
import sys
import json
import concurrent.futures
from dotenv import load_dotenv
from freshdesk.freshdesk_service import FreshdeskService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from service_methods import saveVectorsLocally, createFile, convert_set_to_list, openFile, get_title_by_id

load_dotenv() 

freshdeskService = FreshdeskService("https://umstel.freshdesk.com/api/v2", os.environ.get("FRESHDESK_API_KEY"), 'help.stockstrader.com')

def saveArticles(freshdeskService, save_path):
    text = ''
    articles = freshdeskService.get_all_articles()
    for article in articles:
        text += article + '\n'
    createFile(save_path, text)
    
def save_languages(freshdeskService, save_path):
    languages = convert_set_to_list(freshdeskService.get_languages_by_article_id())      
    languages_json = json.dumps(languages, indent=4)
    createFile(save_path, str(languages_json))


def merge_files(file1_path, file2_path, output_path):
    with open(file1_path, 'r', encoding='utf-8') as f1, \
         open(file2_path, 'r', encoding='utf-8') as f2, \
         open(output_path, 'w', encoding='utf-8') as out:
        out.write(f1.read()) 
        out.write(f2.read())
        
def merge_dict_files(file1, file2, output_file=None):
    with open(file1, 'r', encoding='utf-8') as f:
        dict1 = json.load(f)
    with open(file2, 'r', encoding='utf-8') as f:
        dict2 = json.load(f)
    dict1.update(dict2)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as out:
            json.dump(dict1, out, ensure_ascii=False, indent=2)
    return dict1

def remove_articles_by_ids(filename, article_ids):
    article_ids = set(str(aid) for aid in article_ids)
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    article_blocks = re.split(r'(?m)^# ', text)
    if not article_blocks[0].strip():
        article_blocks = article_blocks[1:]
    kept_blocks = []
    for block in article_blocks:
        full_block = '# ' + block.strip('\n')
        markers = re.findall(r'&#([^&#]+)&#', full_block)
        found_ids = set(m.split('|')[0].strip() for m in markers)
        if not (found_ids & article_ids):
            kept_blocks.append(full_block.rstrip())
    out_text = '\n\n'.join(kept_blocks) + '\n' if kept_blocks else ''
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(out_text)


DATA_FOLDER_PATH = "freshdesk/data/" 
FD_ARTICLES_FILE = "freshdesk_articles.txt"
FD_LANGUAGES_BY_ARTICLE_FILE = "fd_languages_by_article_ids.txt"
FD_VECTOR_STORAGE_FILE = "freshdesk_vector_storage"


def run():    
    print('Freshdesk import is started.')
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(saveArticles, freshdeskService, DATA_FOLDER_PATH + FD_ARTICLES_FILE)
            executor.submit(save_languages, freshdeskService, DATA_FOLDER_PATH + FD_LANGUAGES_BY_ARTICLE_FILE)
                  
        saveVectorsLocally(DATA_FOLDER_PATH, FD_VECTOR_STORAGE_FILE, DATA_FOLDER_PATH + FD_ARTICLES_FILE) 
                 
        print('Freshdesk KnowledgeBase is updated.')
    except Exception as e:
        print(f'Error occured while importing the Freshdesk KnowledgeBase. Message: {e}')