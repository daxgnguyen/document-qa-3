import streamlit as st
import sys
from openai import OpenAI

# Working with ChromaDB or Streamlit Community Cloud
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb

# Create ChromaDB Client
chroma_client = chromadb.PersistentClient(path='/workspaces/document-qa-3/news_chromadb')

if 'HW4_VectorDB' not in st.session_state:
    st.session_state.HW4_VectorDB = chroma_client.get_or_create_collection('news_collection')
collection = st.session_state.HW4_VectorDB

# Create OpenAI Client
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["openai_api_key"])

st.write(f"Collection count: {collection.count()}")

# Show title and description.
st.title("Chatbot")
st.write(
    "Chat with the ChatBot based on the news articles!"
)

system_content = ("You are a helpful news reporting chatbot. Answer questions using only the provided news articles.\n\n"
    "When asked to find 'interesting' or 'top' news:\n"
    "- Return a ranked numbered list of articles\n"
    "- For each article explain WHY it is interesting or significant (market impact, controversy, major announcement, etc.)\n"
    "- Include the company name and date\n\n"
    "When asked about a specific topic or company:\n"
    "- Return all relevant articles you find\n"
    "- Summarize the key points from each\n\n"
    "Always clearly state the company name, date, and source URL you are drawing from.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
def get_n_results(prompt: str) -> int:
    p = prompt.lower()
    if "interesting" in p or "most" in p or "top" in p:
        return 8
    return 3

if prompt := st.chat_input("Ask about the news articles..."):
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
        n_results=get_n_results(prompt)
    )

    rag_context = ""
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        doc_id = results['ids'][0][i]
        rag_context += f"\n\n--- Article: {doc_id} ---\n{doc[:3000]}"

    augmented_system = system_content + f"\n\nRelevant news articles:{rag_context}"
    llm_messages = [{"role": "system", "content": augmented_system}] + st.session_state.messages

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=llm_messages,
        stream=True
    )
    with st.chat_message("assistant"):
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})

    # Store last 5 interactions
    if len(st.session_state.messages) > 10:
        st.session_state.messages = st.session_state.messages[-10:]