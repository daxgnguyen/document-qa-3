import streamlit as st
import requests
from openai import OpenAI
from anthropic import Anthropic
from bs4 import BeautifulSoup


# Show title and description.
st.title("📄 Document question answering")
st.write(
    "Upload a url below and ask a question about it – GPT will answer! "
    )

# Create summary type selection
summary_type = st.sidebar.radio(
    "Select summary type:",
    options=[
        "Summarize the url content in 100 words",
        "Summarize the url content in 2 connecting paragraphs",
        "Summarize the url content in 5 bullet points"
    ]
)s

output_language = st.sidebar.selectbox(
      "Output language:",
      options=["English", "French", "Vietnamese"]
  )

# LLM selection
llm_choice = st.sidebar.selectbox(
      "Select LLM:",
      options=["OpenAI", "Claude"]
  )

# Model selection
use_advanced = st.sidebar.checkbox("Use advanced model")

 # Create an OpenAI client.
openai_client = OpenAI(api_key=st.secrets["openai_api_key"])
antrhopic_client = Anthropic(api_key=st.secrets["clade_api_key"])

def read_url_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text()
    except requests.RequestException as e:
        print(f"Error reading {url}: {e}")
        return None

# Let the user upload a url.
url = st.text_input("Enter a URL:")

# Ask the user for a question via `st.text_area`.
question = st.text_area(
    "Now ask a question about the site!",
    placeholder="Can you give me a short summary?",
    disabled=not url,
)

if url and question:

    # Process the url and question.
    document = read_url_content(url)
    messages = [
        {
            "role": "user",
            "content": f"Here's a document: {document} \n\n---\n\n {question} \n\n Respond in {output_language}.",
        }
    ]

    # Generate an answer depending on the model.
    if llm_choice == "OpenAI":
        stream = openai_client.chat.completions.create(
            model="gpt-5-nano" if use_advanced else "gpt-5-mini",
            messages=messages,
            stream=True,
        )
        st.write_stream(stream)
    else:
        response = antrhopic_client.messages.create(
            model = "claude-sonnet-4-5-20250929" if use_advanced else "claude-haiku-4-5-20251001",
            max_tokens = 1024,
            messages=messages,
        )
        st.write(response.content[0].text)    
