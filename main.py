import os
import streamlit as st
from groq import Groq
from deep_translator import GoogleTranslator
from indic_transliteration.sanscript import transliterate, DEVANAGARI, HK
from streamlit_javascript import st_javascript

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing. Set it in your environment or Streamlit secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="GyanVaani", page_icon="🦙")
st.title("🎓 GyanBot– AI for Everyone")

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
    if st.button("🇬🇧 English"):
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
    translated_content = translate_text(msg["content"], st.session_state.language)
    with st.chat_message(msg["role"]):
        st.markdown(translated_content)

st.subheader("🎙️ Voice Input")
st.markdown("Click the mic and speak your query...")

if st.button("🎤 Speak Now"):
    voice_text = st_javascript(
    """
    async () => {
        if (!('webkitSpeechRecognition' in window)) {
            alert("Your browser does not support voice recognition. Use Chrome.");
            return "";
        }

        return new Promise((resolve) => {
            const recognition = new webkitSpeechRecognition();
            recognition.lang = 'en-US';
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                resolve(transcript);
            };

            recognition.onerror = (event) => {
                console.error("Speech recognition error:", event.error);
                resolve("");
            };

            recognition.onnomatch = () => {
                alert("Speech not recognized. Try again.");
                resolve("");
            };

            try {
                recognition.start();
            } catch (err) {
                alert("Recognition already started. Refresh the page.");
                resolve("");
            }
        });
    }
    """
)
else:
    voice_text = ""

prompt = voice_text or st.chat_input("Ask something...")

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

        translated_reply = translate_text(reply, st.session_state.language)
        with st.chat_message("assistant"):
            st.markdown(translated_reply)

    except Exception as e:
        st.error(f"Error: {e}")
