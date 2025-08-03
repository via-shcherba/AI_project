from freshdesk.freshdesk_API import FreshdeskAPI
from freshdesk.ban_articles import ban_articles

class FreshdeskService():
    
    def __init__(self, base_url, api_key, source_url):
        self.freshdesk = FreshdeskAPI(base_url, api_key)
        self.primary_language = self.get_primary_language()
        self.source_url = source_url
        
        
    def get_primary_language(self):
        response = self.freshdesk.get_languages()
        if response.status_code == 200:
            languageJson = response.json()
            return languageJson['primary_language']
        
        
    def get_all_supported_languages(self):
        all_languages = []
        response = self.freshdesk.get_languages()
        if response.status_code == 200: 
            languageJson = response.json()
            all_languages.append(languageJson['primary_language'])
            all_languages.extend(languageJson['supported_languages'])
            return all_languages          
    
        
    def get_all_articles(self):
        try:
            documents = list()
            for folder in self.get_all_folders():
                response = self.freshdesk.get_articles(folder['id'], self.primary_language)
                if response.status_code == 200:          
                    for article in response.json():
                        article_id = str(article['id'])
                        if (article['status'] == 2 and article_id not in ban_articles):
                            document = ''
                            document += '# ' + folder['category_name'] + ' (' + folder['category_description'] + ')' + ' / ' + folder['folder_name'] + ' ' + article['title'] + '\n'
                            document += folder['category_name'] + ' / ' + folder['folder_name'] + ': ' + article['title'] + '\n'
                            document += folder['category_name'] + ' / ' + folder['folder_name'] + ': ' + article['description_text'] + '\n'
                            document += '&#' + article_id + '|' + self.source_url + '&#\n'
                            documents.append(document)
            return tuple(documents)
        except Exception as e:
            print('Error in get_all_articles: ' + e)
    
    
    def get_languages_by_article_id(self):
        languages_by_article_id = {}
        supported_languages = self.get_all_supported_languages()
        folders = self.get_all_folders()
        for folder in folders:
            for language in supported_languages:                     
                response = self.freshdesk.get_articles(folder['id'], language)
                if response.status_code == 200:                 
                    for article in response.json():                                                 
                        if (article['status'] == 2):   
                            articleId = str(article['id'])                                
                            if articleId in languages_by_article_id:
                                existed_languages = languages_by_article_id.get(articleId)
                                existed_languages.add(language)
                                languages_by_article_id.update({articleId : existed_languages})
                            else:
                                languages = set()
                                languages.add(language)                                                                                                                                        
                                languages_by_article_id.update({articleId : languages})
                                                                                                    
        return languages_by_article_id
        
    
    def get_all_folders(self):
        try:
            result = []
            categories = self.get_all_categories()
            for category in categories:
                category_id = str(category.get('id'))
                category_name = category.get('name')
                category_description = category.get('description')
                response = self.freshdesk.get_folders(category_id, self.primary_language)
                if response.status_code == 200:
                    try:
                        folder_list = response.json()  
                        for folder in folder_list:
                            result.append({
                                'id': str(folder.get('id')),
                                'folder_name': folder.get('name'),
                                'category_name': category_name,
                                'category_description': category_description
                            })
                    except Exception as e:
                        print(f'Error parsing folders for category {category_id}: {e}')
                else:
                    print(f'Failed to get folders for category {category_id}: {response.status_code} {response.content}')
            return result
        except Exception as e:
            print('Error in get_all_folders: ' + e)
    
    
    def get_all_categories(self):
        response = self.freshdesk.get_categories()
        categories = []
        if response.status_code == 200:
            try:
                articles = response.json()  
                for article in articles:
                    cat = {
                        'id': article.get('id'),
                        'name': article.get('name'),
                        'description': article.get('description')
                    }
                    categories.append(cat)
            except (ValueError, KeyError, TypeError) as e:
                print(f'Error parsing categories: {e}')
        else:
            print(f'Failed to get categories: {response.status_code} {response.content}')
        return categories