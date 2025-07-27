import os
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
from deep_translator import GoogleTranslator
from indic_transliteration.sanscript import transliterate, DEVANAGARI, HK
from streamlit_javascript import st_javascript

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing. Set it in environment or Streamlit secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="GyanVaani", page_icon="🦙", layout="wide")
st.markdown("""
    <style>
    .stChatInputContainer { position: fixed; bottom: 0; width: 100%; z-index: 1000; background: white; padding: 10px 0; }
    .block-container { padding-bottom: 120px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='margin-top: 0;'>🎓 GyanBot – Chat with LLaMA 3.1 + Translation + Voice</h1>", unsafe_allow_html=True)

if "language" not in st.session_state:
    st.session_state.language = "original"

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🔁 Original"):
        st.session_state.language = "original"
with col2:
    if st.button("🇮🇳 Hindi"):
        st.session_state.language = "hindi"
with col3:
    if st.button("🇺🇸 English"):
        st.session_state.language = "english"
with col4:
    if st.button("🇮🇳🅰 Hinglish"):
        st.session_state.language = "hinglish"

def translate_text(text, target):
    if target == "original":
        return text
    try:
        if target == "hinglish":
            hindi_text = GoogleTranslator(source='auto', target='hi').translate(text)
            return transliterate(hindi_text, DEVANAGARI, HK)
        else:
            lang_code = "hi" if target == "hindi" else "en"
            return GoogleTranslator(source='auto', target=lang_code).translate(text)
    except Exception as e:
        return f"(Translation failed) {text} ({e})"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    translated = translate_text(msg["content"], st.session_state.language)
    with st.chat_message(msg["role"]):
        st.markdown(translated)

voice_script = """
await new Promise((resolve) => {
  const mic = document.createElement("button");
  mic.innerText = "🎤";
  mic.style.marginRight = "10px";
  mic.style.fontSize = "20px";
  mic.onclick = () => {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = "hi-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.start();
    recognition.onresult = (event) => {
      const textBox = document.querySelector("textarea");
      if (textBox) {
        textBox.value = event.results[0][0].transcript;
        textBox.dispatchEvent(new Event('input', { bubbles: true }));
        setTimeout(() => {
          const form = textBox.closest("form");
          if (form) form.dispatchEvent(new Event('submit', { bubbles: true }));
        }, 500);
      }
    };
  };
  const container = document.querySelector(".stChatInputContainer");
  if (container && !container.querySelector("button")) {
    container.prepend(mic);
  }
});
"""
st_javascript(voice_script)

text_input = st.chat_input("Type something or click mic...")
if text_input:
    st.chat_message("user").markdown(text_input)
    st.session_state.chat_history.append({"role": "user", "content": text_input})

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                *st.session_state.chat_history,
            ]
        )
        reply = response.choices[0].message.content
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(translate_text(reply, st.session_state.language))
    except Exception as e:
        st.error(f"Error: {e}")
