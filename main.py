import os
import streamlit as st
import requests
from groq import Groq
from deep_translator import GoogleTranslator
from indic_transliteration.sanscript import transliterate, DEVANAGARI, ITRANS, HK


# ===================== API Key ===================== #
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY is missing. Set it in your environment or Streamlit secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# ============ Streamlit UI Settings ============ #
st.set_page_config(page_title="LLAMA 3.1 Chat", page_icon="🦙")
st.title("🦙 LLAMA 3.1 ChatBot")

# ============ Language Selector ============ #
if "language" not in st.session_state:
    st.session_state.language = "original"  # default

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🔁 Original"):
        st.session_state.language = "original"
with col2:
    if st.button("🇮🇳 Hindi"):
        st.session_state.language = "hindi"
with col3:
    if st.button("🇬🇧 English"):
        st.session_state.language = "english"
with col4:
    if st.button("🇮🇳🅰 Hinglish"):
        st.session_state.language = "hinglish"

# ============ Translator ============ #
def translate_text(text, target):
    if target == "original":
        return text
    try:
        if target == "hinglish":
            # 1. Translate to Hindi
            hindi_text = GoogleTranslator(source='auto', target='hi').translate(text)
            # 2. Transliterate Hindi to Latin
            return transliterate(hindi_text, DEVANAGARI, HK)  # or SLP1
        else:
            lang_code = "hi" if target == "hindi" else "en"
            return GoogleTranslator(source='auto', target=lang_code).translate(text)
    except Exception as e:
        return f"(Translation failed) {text} ({e})"

# ============ Chat Memory ============ #
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ============ Display History ============ #
for msg in st.session_state.chat_history:
    translated_content = translate_text(msg["content"], st.session_state.language)
    with st.chat_message(msg["role"]):
        st.markdown(translated_content)

# ============ User Input ============ #
prompt = st.chat_input("Ask something...")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    try:
        # Call Groq LLAMA 3
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                *st.session_state.chat_history
            ]
        )
        reply = response.choices[0].message.content
        st.session_state.chat_history.append({"role": "assistant", "content": reply})

        translated_reply = translate_text(reply, st.session_state.language)
        with st.chat_message("assistant"):
            st.markdown(translated_reply)

    except Exception as e:
        st.error(f"❌ Error: {e}")
