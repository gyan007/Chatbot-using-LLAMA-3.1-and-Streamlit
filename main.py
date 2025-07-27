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
        #custom-input {
            position: fixed;
            bottom: 10px;
            left: 0;
            right: 0;
            padding: 10px;
            background-color: #f9f9f9;
            display: flex;
            justify-content: center;
            gap: 5px;
            box-shadow: 0 -2px 8px rgba(0,0,0,0.1);
            z-index: 9999;
        }
        #chat-container {
            margin-bottom: 80px;
        }
        .msg {
            background: #f1f1f1;
            padding: 10px;
            margin: 5px 0;
            border-radius: 10px;
        }
        .user { background-color: #d1e7dd; }
        .assistant { background-color: #fff3cd; }
    </style>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "language" not in st.session_state:
    st.session_state.language = "original"

def translate_text(text, target):
    if target == "original":
        return text
    try:
        if target == "hinglish":
            hindi_text = GoogleTranslator(source='auto', target='hi').translate(text)
            return transliterate(hindi_text, DEVANAGARI, HK)
        lang_code = "hi" if target == "hindi" else "en"
        return GoogleTranslator(source='auto', target=lang_code).translate(text)
    except Exception as e:
        return f"(Translation failed) {text} ({e})"

with st.container():
    st.markdown("<div id='chat-container'>", unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        translated = translate_text(msg["content"], st.session_state.language)
        role_class = "user" if msg["role"] == "user" else "assistant"
        st.markdown(f"<div class='msg {role_class}'><strong>{msg['role'].capitalize()}:</strong> {translated}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

components.html(
    """
    <div id="custom-input">
        <button onclick="startRecognition()">🎤</button>
        <input id="voice-text" type="text" placeholder="Type or Speak..." style="flex: 1; padding: 10px;"/>
        <button onclick="sendMessage()">Send</button>
    </div>
    <script>
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'hi-IN';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        function startRecognition() {
            recognition.start();
        }

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            document.getElementById("voice-text").value = transcript;
        };

        function sendMessage() {
            const text = document.getElementById("voice-text").value;
            window.parent.postMessage({type: 'SEND_CHAT', text: text}, '*');
            document.getElementById("voice-text").value = '';
        }
    </script>
    """,
    height=100
)

message = st_javascript("""
    await new Promise((resolve) => {
        window.addEventListener("message", (event) => {
            if (event.data.type === "SEND_CHAT") {
                resolve(event.data.text);
            }
        });
    });
""")

if message and isinstance(message, str) and message.strip():
    st.session_state.chat_history.append({"role": "user", "content": message})
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
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Error: {e}")
