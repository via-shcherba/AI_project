import re
import pytz
from datetime import datetime


def createFile(save_path, content):    
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
def openFile(file_path):
    file = open(file_path, 'r', encoding='utf-8')
    return file.read()    
            
def convert_set_to_list(dictionary):
    output_dict = {}   
    for key, value in dictionary.items():        
        output_dict[key] = list(value) 
    return output_dict
       
def converStringToListOfLists(str):
    result = []
    for listStr in str.split('<#>'):
        if (len(listStr) > 0):           
            result.append(listStr.split('<|>'))
    return result

def convertListOfListsToString(listOfLists):
    result = ''
    size = len(listOfLists) - 1
    for i, listStr in enumerate(listOfLists):
        if (len(listStr) > 0):
            result += listStr[0] + '<|>' + listStr[1].replace('\\', '')
        if (i != size):
            result += '<#>'
    return result

def extract_comand_and_message(input_string):
    start_marker = '#*'
    end_marker = '*#'
    start_index = input_string.find(start_marker)
    end_index = input_string.find(end_marker)
    
    if start_index == -1 or end_index == -1:
        return input_string, None

    command = input_string[start_index + len(start_marker):end_index]
    return command

def read_files_to_dict(base_path, file_paths):
    result = {}
    for key, file_path in file_paths.items():
        try:         
            result[key] = openFile(base_path + file_path)
        except FileNotFoundError:
            result[key] = f"Error: file '{file_path}' not found."
        except Exception as e:
            result[key] = f"Error: {str(e)}"
    return result

def convert_string_to_dict(json_string):
    import json
    data_dict = json.loads(json_string)  
    return data_dict

def convert_file_to_dict(file_path): 
    file = open(file_path, 'r', encoding='utf-8')
    data = convert_string_to_dict(file.read())
    return data

def replace_k_base_article_handling(text, replacement):
    pattern = r'Knowledge Base Article Handling:(.*?)(?=\n\n)'
    return re.sub(pattern, replacement, text, flags=re.DOTALL).strip()

def convert_from_cyprus_time(cyprus_time_str, user_timezone_str):
    current_date = datetime.now().date()
    cyprus_tz = pytz.timezone('Asia/Nicosia')
    cyprus_time = datetime.strptime(cyprus_time_str, '%H:%M')
    cyprus_time = datetime.combine(current_date, cyprus_time.time())
    cyprus_time = cyprus_tz.localize(cyprus_time)
    user_tz = pytz.timezone(user_timezone_str)
    user_time = cyprus_time.astimezone(user_tz)
    return user_time.strftime('%H:%M')

def extract_and_replace_trading_sessions(input_str, user_timezone_str):
    pattern = r'&#(.*?)&#'
    tag_re = re.compile(r'<[^>]+>')
    def replace_with_list(match):
        inner_text = match.group(1)
        clean_text = tag_re.sub('', inner_text)
        converted_time = convert_from_cyprus_time(clean_text, user_timezone_str)
        return f'{converted_time} ({user_timezone_str})'
    return re.sub(pattern, replace_with_list, input_str)

def extract_and_replace_help_centere_url(text, language, languages_by_article):
    if not language or not languages_by_article:
        return text
    pattern = r'&#(\d+)\|([^\s&#]+)&#'
    def replacer(match):
        article_id = match.group(1)
        domain = match.group(2)
        url = get_help_centere_article_url(article_id, language, languages_by_article, domain)
        return f"\nSource: {url}"
    return re.sub(pattern, replacer, text)

def get_help_centere_article_url(article_id, language, languages_by_article, domain):
    lang_code = lang_codes.get(language)
    check_result = get_language_by_article_id(languages_by_article, article_id, lang_code)
    if not check_result:
        lang_code = 'en'
    return f'https://{domain}/{lang_code}/support/solutions/articles/{article_id}'
        
def get_language_by_article_id(languages_by_article, article_id, language_code):
    result = False
    languages = languages_by_article.get(article_id, [])
    if language_code in languages:
        result = True  
    return result

lang_codes = {
    'English': 'en',
    'Russian': 'ru-RU',
    'Portuguese': 'pt-BR',
    'Arabic': 'ar',
    'Czech': 'cs',
    'German': 'de',
    'Spanish': 'es-LA',
    'Thai': 'th'
}

def extract_tickers(text, stopwords):
    pattern = r'\b[A-Z]{1,6}(?:[.\-][A-Z0-9]{1,4})?\b'
    found = re.findall(pattern, text)
    return [word for word in found if word.upper() not in stopwords]