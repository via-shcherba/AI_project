import os
from langchain_core.tools import Tool # type: ignore
from langchain_google_community import GoogleSearchAPIWrapper # type: ignore
import asyncio


class Google_SE:
    

    def __init__(self, google_cse_id, google_api_key):       
        self.search = GoogleSearchAPIWrapper(google_api_key=google_api_key, google_cse_id=google_cse_id)
            
    
    async def top_results(self, query):
        return await asyncio.to_thread(self.search.results, query, 4)
        
        
    def prepare_articles(self, search_results):
        show_links = False
        if show_links:
            article_generator = (
                f"\nInternet Article №{i+1}\n{article['title']}\n{article['snippet']}\nLink: {article['link']}"
                for i, article in enumerate(search_results)
                if all(article.get(key) for key in ['title', 'snippet', 'link'])
            )
        else:
            article_generator = (
                f"\nInternet Article №{i+1}\n{article['title']}\n{article['snippet']}"
                for i, article in enumerate(search_results)
                if all(article.get(key) for key in ['title', 'snippet'])
            )
        return "\n".join(article_generator)
        
    
    async def getArticles(self, request):
        tool = Tool(
            name="Google Search Snippets",
            description="Search Google for recent results.",
            func=self.top_results,
        )
        search_results = await tool.func(request)
        return self.prepare_articles(search_results)