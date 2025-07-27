import os
import streamlit as st
from groq import Groq

# Load API key securely
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY is missing. Please set it in your environment or Streamlit secrets.")
    st.stop()

# Initialize client
client = Groq(api_key=GROQ_API_KEY)

# Chat logic
st.set_page_config(page_title="LLAMA 3.1. Chat", page_icon="🦙")
st.title("🦙 LLAMA 3.1. ChatBot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask something...")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                *st.session_state.chat_history
            ]
        )
        reply = response.choices[0].message.content
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
    except Exception as e:
        st.error(f"❌ Error: {e}")
