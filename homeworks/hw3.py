import streamlit as st
import requests
from openai import OpenAI
from anthropic import Anthropic
from bs4 import BeautifulSoup

# Show title and description.
st.title("Chatbot")
st.write(
    "Input up to two urls and get a response from your desired AI based on the URL's content! "
)

# LLM selection

llm_choice = st.sidebar.selectbox(
    "Select LLM:",
    options=["OpenAI", "Claude"]
)

# LLMs
openai_client = OpenAI(api_key=st.secrets["openai_api_key"])
anthropic_client = Anthropic(api_key=st.secrets["claude_api_key"])

# URL Inputs
url1 = st.sidebar.text_input("URL 1:")
url2 = st.sidebar.text_input("URL 2:")

def read_url_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text()
    except requests.RequestException as e:
        print(f"Error reading {url}: {e}")
        return None

# System prompt for url context
system_content = "You are to read and understand the content of the URL, and provide a response tailed to the input from the user "
if url1:
    content1 = read_url_content(url1)
    if content1:
        system_content += f"\n\nURL 1 content: {content1}"
if url2:
    content2 = read_url_content(url2)
    if content2:
        system_content += f"\n\nURL 2 content: {content2}"

# Initialize chat history with system prompt
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_content}]

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input 
if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    if llm_choice == "OpenAI":
        stream = openai_client.chat.completions.create(
            model="gpt-5-nano",
            messages=st.session_state.messages,
            stream=True
        )
        with st.chat_message("assistant"):
            response = st.write_stream(stream)
    else:
        result = anthropic_client.messages.create(
            model= "claude-sonnet-4-5-20250929",
            max_tokens=1024,
            system=st.session_state.messages[0]["content"],
            messages=[m for m in st.session_state.messages if m["role"] != "system"]
        )
        response = result.content[0].text
        with st.chat_message("assistant"):
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

# Conversation summary after 6 messages
non_system = [m for m in st.session_state.messages if m["role"] != "system"]
if len(non_system) > 6:
    convo_text = ""
    for m in non_system [:-6]:
        convo_text += f"{m['role']}: {m['content']}\n"
    
    # Get OpenAI summarys
    summary_response = openai_client.chat.completions.create(
        model="gpt-5-nano",
            messages=[
                {"role": "user", "content": f"Summarize this conversation in 2-3 sentences:\n\n{convo_text}"}
            ])

    summary = summary_response.choices[0].message.content

    st.session_state.messages = [
        st.session_state.messages[0],
        {"role": "system", "content": f"Summary of earlier conversation: {summary}"}
    ] + non_system[-6]