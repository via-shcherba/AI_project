import re
import asyncio
from typing import List, Tuple


class Document:
    
    def __init__(self, metadata, page_content, score=None):
        self.metadata = metadata
        self.page_content = page_content
        self.score = score
        

class KnowledgeBaseSearch():
        
    def __init__(self, local_faiss):
        self.local_faiss = local_faiss   
                           

    async def getSearchResult(self, request, show_links):   
        valid_score = 1.3
        docs = await asyncio.to_thread(self.local_faiss.similarity_search_with_score, request, k=4)
        converted_docs = self.convert_documents(docs)
        filtered_docs = [
            (i, doc) for i, doc in enumerate(converted_docs) if doc.score <= valid_score
        ]       
        message_content = re.sub(
            r'\n{2}',
            ' ',
            '\n '.join([
                f'\nKnowledge Base Article №{i+1}\n{self.source_permition(doc.score, doc.page_content, show_links)}'
                for i, doc in filtered_docs
            ])
        )
        return message_content
    
    
    def remove_article_id(self, text):
        article_id_regex = r'&#.*?&#'
        updated_text = re.sub(article_id_regex, '', text).strip()    
        return updated_text
    
    
    def source_permition(self, input_str, text, show_links):
        score = float(input_str)
        if show_links:
            if score <= 0.84:
                return text
            else:
                return self.remove_article_id(text)
        else:
            return self.remove_article_id(text)
    
    
    def convert_documents(self, input_list: List[Tuple[Document, float]]) -> List[Document]:
        return [Document(metadata=doc.metadata, page_content=doc.page_content, score=score) for doc, score in input_list]