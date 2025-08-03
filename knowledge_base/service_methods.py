import os
import re
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv() 

def createFile(save_path, content):    
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
def openFile(file_path):
    file = open(file_path, 'r', encoding='utf-8')
    return file.read()    
        
def clean_text(text):  
    import re
    text = re.sub(r'\xa0', ' ', text)
    text = re.sub(r'\n', ' ', text)      
    return text

def getVectors(data):   
    model = os.environ.get("EMBEDING_MODEL")
    embeddings = OpenAIEmbeddings(model=model)
    return FAISS.from_documents(data, embeddings)
    
def convert_set_to_list(dictionary):
    output_dict = {}   
    for key, value in dictionary.items():        
        output_dict[key] = list(value) 
    return output_dict
   
def splitToChunks(file):   
    from langchain.text_splitter import MarkdownHeaderTextSplitter
    headers_to_split_on = [("#", "Header")]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    fragments = markdown_splitter.split_text(file)

    for i, fragment in enumerate(fragments):
        fragments[i].page_content = clean_text(fragment.page_content)
    return fragments

def saveVectorsLocally(folder_path, file_name, source_file):    
    file = openFile(source_file)
    chunks = splitToChunks(file)
    vectorDB = getVectors(chunks)
    vectorDB.save_local(folder_path=folder_path, index_name=file_name)
    
def getLocalFAISS(folder_path, vectors_file):
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local(
        folder_path = folder_path,
        embeddings = embeddings,
        index_name = vectors_file,
        allow_dangerous_deserialization = True       
    )

def get_title_by_id(content):
    if content is None:
        return ''
    result_dict = {}
    lines = content.splitlines()
    current_title = None
    current_block_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            if current_title is not None:
                block_text = "\n".join(current_block_lines)
                id_match = re.search(r'&#(\d+)&#', block_text)
                if id_match:
                    article_id = id_match.group(1)
                    result_dict[article_id] = current_title
            current_title = line.lstrip('#').strip()
            current_block_lines = []
        else:
            current_block_lines.append(line)
    if current_title is not None:
        block_text = "\n".join(current_block_lines)
        id_match = re.search(r'&#(\d+)&#', block_text)
        if id_match:
            article_id = id_match.group(1)
            result_dict[article_id] = current_title 
    return result_dict