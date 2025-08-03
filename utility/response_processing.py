import re

def replace_language_code_in_links(text, languages_by_article):
    if len(languages_by_article) == 0:
        return text
    url_regex = r'href="(https?://help\.stockstrader\.com/([a-z]{2}(?:-[A-Z]{2})?)/support/solutions/articles/(\d+))"'
    
    def repl(match):
        url = match.group(1)
        language_code = match.group(2)  
        article_id = match.group(3)      
        languages = languages_by_article.get(article_id, [])
       
        if language_code not in languages:
            new_lang_code = 'en'  
        else:
            new_lang_code = language_code
        
        url = url.replace(f'/{language_code}/', f'/{new_lang_code}/')      
        return f'href="{url}"'
    
    updated_text = re.sub(url_regex, repl, text)
    return updated_text

def replace_with_breaks(text):
    return re.sub(r'\n', '<br>', text)

def replace_breaks(text):
    return re.sub(r'<br>', '\n', text)

def replace_double_asterisks_with_bold(text):
    bold_regex = r'\*\*(.*?)\*\*'
    return re.sub(bold_regex, lambda match: f'<b>{match.group(1)}</b>', text)

def highlight_financial_figures(text):
    # Regular expression to match financial figures including percentages with comma as decimal separator
    financial_regex = (
        r'\b(?:\d{1,3}(?:,\d{3})*[\.,]?\d*%|'  # % with both comma and dot as decimal
        r'\$\d{1,3}(?:,\d{3})*(?:\.\d+)?|'  # Dollar amounts
        r'€\d{1,3}(?:,\d{3})*(?:\.\d+)?|'  # Euro amounts
        r'£\d{1,3}(?:,\d{3})*(?:\.\d+)?|'  # Pound amounts
        r'د.إ\d{1,3}(?:,\d{3})*(?:\.\d+)?|'  # Dirham amounts
        r'[\d,]+[\s]*[↑↓])'  # Numbers with increase/decrease indicators
    )
    return re.sub(financial_regex, lambda match: f'<u><b>{match.group(0)}</b></u>', text)

def make_numbers_bold(text):
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    for idx, url in enumerate(urls):
        text = text.replace(url, f'__URL{idx}__')  
    number_pattern = r'\b\d+\b'
    text = re.sub(number_pattern, r'<b>\g<0></b>', text)
    for idx, url in enumerate(urls):
        text = text.replace(f'__URL{idx}__', url)
    return text

def format_response(response):
    formatted_response = replace_with_breaks(response)
    formatted_response = highlight_urls(formatted_response)
    formatted_response = replace_double_asterisks_with_bold(formatted_response)
    formatted_response = highlight_financial_figures(formatted_response) 
    formatted_response = make_numbers_bold(formatted_response)
    return formatted_response

def remove_b_tags(text):
    return text.replace('<b>', '').replace('</b>', '')

def remove_u_tags(text):
    return re.sub(r'</?u>', '', text)

def replace_anchor_with_url(text):
    return re.sub(r'<a href="(.*?)".*?>(.*?)</a>', r'\1', text)

def format_history(text):
    text = replace_breaks(text)
    text = remove_b_tags(text)
    text = remove_u_tags(text)
    return replace_anchor_with_url(text)

def highlight_stock_trader(text):    
    stocks_trader_pattern = r'\b(R? StocksTrader)\b(?![^<]*</a>)'
    def replace_stocks_trader(match):
        return r'<a href="https://stockstrader.com" target="_blank">{}</a>'.format(match.group(1))

    updated_text = re.sub(stocks_trader_pattern, replace_stocks_trader, text)
    return updated_text

def clean_html(text):        
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def highlight_urls(text):
    url_pattern = re.compile(
        r'''(?i)\b((?:https?://|www\.)[^\s<>'"()]+)''',
    )
    def replace_url(match):
        url = match.group(1)
        href = url if url.startswith('http') else f'http://{url}'
        return f'<a href="{href}" target="_blank">{url}</a>'
    return url_pattern.sub(replace_url, text)