import streamlit as st
import requests
import sys
from pathlib import Path
from openai import OpenAI
from anthropic import Anthropic
from bs4 import BeautifulSoup

# Working with ChromaDB or Streamlit Community Cloud
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb

# Create ChromaDB Client
chroma_client = chromadb.PersistentClient(path='./chromaD3_for_HW')

if 'HW4_VectorDB' not in st.session_state:
    st.session_state.HW4_VectorDB = chroma_client.get_or_create_collection('HW4Collection')
collection = st.session_state.HW4_VectorDB

# Create OpenAI Client
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["openai_api_key"])

def add_to_collection(collection, text, file_name):
    
    # Create an embedding
    client = st.session_state.openai_client
    response = client.embeddings.create(
        input=text,
        model='text-embedding-3-small'
    )
    
    # Get the embedding
    embedding = response.data[0].embedding
    
    # Add embedding to ChromaDB
    collection.add(
        documents=[text],
        ids=[file_name],
        embeddings=[embedding]
    )

# Extract Text from PDF
def extract_text_from_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    return soup.get_text()

st.write(f"Collection count: {collection.count()}")

# Semantic chunking, split the document into chunks at the nearest boundary
# Documents have clear sections, easier and cheaper way of chunking

def chunk_text(text):
    midpoint = len(text) // 2
    split_point = text.find('.', midpoint)
    if split_point == -1:
        split_point = midpoint
    else:
        split_point += 1 #include period
    chunk1 = text[:split_point].strip()
    chunk2 = text[split_point:].strip()
    return [chunk1, chunk2]

def load_content_to_collection(folder_path, collection):
    if collection.count() == 0:
        content_folder = Path(folder_path)
        for html_file in content_folder.glob("*.html"):
            text = extract_text_from_html(html_file)
            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                chunk_id = f"{html_file.name}_chunk{i+1}"
                add_to_collection(collection, chunk, chunk_id)

loaded = load_content_to_collection('./HW-04-Data/su_orgs', collection)

# Show title and description.
st.title("Chatbot")
st.write(
    "Chat with the ChatBot based on the organization profile! "
)

system_content = (
    "You are a helpful organization chatbot. When you answer use information from the profile pages. Clearly state where you are drawing information from organization profiles.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about Syracuse University organization profiles..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = st.session_state.openai_client
    query_response = client.embeddings.create(
        input=prompt,
        model='text-embedding-3-small'
    )
    query_embedding = query_response.data[0].embedding
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    rag_context = ""
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        doc_id = results['ids'][0][i]
        rag_context += f"\n\n--- Document: {doc_id} ---\n{doc[:3000]}"

    augmented_system = system_content + f"\n\nRelevant course documents:{rag_context}"
    llm_messages = [{"role": "system", "content": augmented_system}] + st.session_state.messages

    stream = client.chat.completions.create(
        model="gpt-5-mini",
        messages=llm_messages,
        stream=True
    )
    with st.chat_message("assistant"):
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})

    # Store last 5 interactions
    if len(st.session_state.messages) > 10:
        st.session_state.mssages = st.session_state.messages[-10:]