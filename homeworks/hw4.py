import streamlit as st
import requests
import sys
from PyPDF2 import PdfReader
from pathlib import Path
from openai import OpenAI
from anthropic import Anthropic
from bs4 import BeautifulSoup

# Working with ChromaDB or Streamlit Community Cloud
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb

# Create ChromaDB Client
chroma_client = chromadb.PersistentClient(path='./chromaD3_for_Lab')

if 'Lab4_VectorDB' not in st.session_state:
    st.session_state.Lab4_VectorDB = chroma_client.get_or_create_collection('Lab4Collection')
collection = st.session_state.Lab4_VectorDB

# LLM selection

llm_choice = st.sidebar.selectbox(
    "Select LLM:",
    options=["OpenAI", "Claude"]
)

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
def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

st.write(f"Collection count: {collection.count()}")

def load_pdfs_to_collection(folder_path, collection):
    if collection.count() == 0:
        pdf_folder = Path(folder_path)
        for pdf_file in pdf_folder.glob("*.pdf"):
            text = extract_text_from_pdf(pdf_file)
            add_to_collection(collection, text, pdf_file.name)

loaded = load_pdfs_to_collection('./HW-04-Data/su_orgs', collection)

# Show title and description.
st.title("Chatbot")
st.write(
    "Chat with the ChatBot based on the course content! "
)

system_content = (
    "You are a helpful course information chatbot. When you answer use information from the course documents. Clearly state where you are drawing information from course materials.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about course content..."):
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