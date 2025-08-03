import os
import requests

    
class FreshdeskAPI():
    
    def __init__(self, base_url, api_key):
        self.api_key = api_key
        self.base_url = base_url
        self.password = ""
        
        
    def get_categories(self):
        url = self.base_url + "/solutions/categories"
        return requests.get(url, auth = (self.api_key, self.password))
    
    
    def get_languages(self):
        url = self.base_url + "/settings/helpdesk"
        return requests.get(url, auth = (self.api_key, self.password))
    

    def get_folders(self, id: str, language: str):
        url = self.base_url + "/solutions/categories/" + id + "/folders/" + language
        return requests.get(url, auth = (self.api_key, self.password))
    
    
    def get_articles(self, id: str, language: str):
        url = self.base_url + "/solutions/folders/" + id + "/articles/" + language
        return requests.get(url, auth = (self.api_key, self.password))
    
    
def get_sections_info(sections):
    result = []
    for section in sections:
        result.append({
            'id': section['id'],
            'name': section['name'],
            'description': section['description']
        })
    return result

# import json
# fd = FreshdeskAPI('https://umstel.freshdesk.com/api/v2', '9Js11CrGVtiU9Non2nqS')
# res = fd.get_folders('33000138893', 'en')

# print(res.json())