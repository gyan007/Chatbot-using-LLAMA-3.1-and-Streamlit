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


st.set_page_config(page_title="GyanVaani", page_icon="🦙")
st.title("🎓 GyanBot – Chat with LLaMA 3.1 + Translation + Voice")


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



st.subheader("🎙 Voice Input (Browser-Based)")

components.html(
    """
    <button onclick="startRecognition()" style="font-size:18px;padding:10px 20px;">🎤 Click to Speak</button>
    <p id="transcript" style="font-size:16px;color:green;"></p>
    <script>
        var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'hi-IN';  // Change to 'en-IN' or 'en-US' for Hinglish/English
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        function startRecognition() {
            document.getElementById("transcript").innerText = "🎧 Listening...";
            recognition.start();
        }

        recognition.onresult = function(event) {
            var transcript = event.results[0][0].transcript;
            window.parent.postMessage({type: 'SPEECH_RESULT', text: transcript}, '*');
            document.getElementById("transcript").innerText = "🗣 You said: " + transcript;
        };
    </script>
    """,
    height=200,
)


speech_result = st_javascript("""await new Promise((resolve) => {
  window.addEventListener("message", (event) => {
    if (event.data.type === "SPEECH_RESULT") {
      resolve(event.data.text);
    }
  });
});""")


if speech_result and isinstance(speech_result, str) and speech_result.strip():
    st.session_state["autofill_input"] = speech_result.strip()

text_input = st.chat_input("Type something or use voice...", key="chat_input")


if "autofill_input" in st.session_state:
    prompt = st.session_state.pop("autofill_input")
else:
    prompt = text_input.strip() if text_input else None



if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.chat_history.append({"role": "user", "content": prompt})

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
