import os
import sys
from dotenv import load_dotenv # type: ignore
from langchain_openai import OpenAIEmbeddings # type: ignore
from langchain_community.vectorstores import FAISS # type: ignore

CURRENT_DIR = os.path.dirname(__file__)

sys.path.extend([
    os.path.abspath(os.path.join(CURRENT_DIR, '../', dir_name))
    for dir_name in ['utility']
])

from bot_service_methods import convert_file_to_dict # type: ignore


class Help_KB_Init:

    
    def __init__(self, vector_storage_path, vector_storage_file, article_languages_file):
        load_dotenv()
        open_ai_key = os.environ.get("KB_OPENAI_API_KEY")
        self.faiss = FAISS
        self.embeddings = OpenAIEmbeddings(model='text-embedding-3-large', openai_api_key=open_ai_key)
        self.local_faiss = self.getLocalFAISS(vector_storage_path, vector_storage_file)
        self.languages_by_article_id = convert_file_to_dict(article_languages_file)

    
    def getLocalFAISS(self, folder_path, vectors_file):
        return self.faiss.load_local(
            folder_path = folder_path,
            embeddings = self.embeddings,
            index_name = vectors_file,
            allow_dangerous_deserialization = True       
        )