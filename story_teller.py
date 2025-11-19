import streamlit as st
from openai import OpenAI
import os
import base64
from io import BytesIO

# Load environment variables

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Streamlit setup
st.set_page_config(
    page_title="📚 Historical Storyteller for Kids",
    page_icon="📜",
    layout="centered"
)

# 🎨 Custom CSS
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #ffeecf, #fbd786);
    font-family: 'Poppins', sans-serif;
}
.user-msg, .ai-msg {
    padding: 15px 20px;
    border-radius: 15px;
    margin: 10px 0;
    max-width: 80%;
    line-height: 1.5;
}
.user-msg {
    background-color: #f4a261;
    color: white;
    align-self: flex-end;
    margin-left: auto;
}
.ai-msg {
    background-color: #fff7e6;
    border: 2px solid #f4a261;
    color: #333;
    align-self: flex-start;
}
.stTextInput>div>div>input {
    border-radius: 10px !important;
}
.stButton>button {
    background-color: #f4a261 !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    height: 40px;
    transition: 0.3s;
}
.stButton>button:hover {
    background-color: #e76f51 !important;
}
.chat-container {
    display: flex;
    flex-direction: column;
}
</style>
""", unsafe_allow_html=True)

# Title
st.title("📜 Historical Storyteller for Kids")
st.caption("Ask for stories, listen to them, and edit your queries just like in ChatGPT!")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None
if "story_history" not in st.session_state:
    st.session_state.story_history = []  # keep all completed stories

# --- Function to generate AI response ---
def generate_story(conversation):
    with st.spinner("Weaving your story... ✨"):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation,
            temperature=0.9,
            max_tokens=500
        )
    return response.choices[0].message.content

# --- Function for TTS (text to speech) ---
def text_to_speech(text):
    with st.spinner("🎧 Preparing your story narration..."):
        speech = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text
        )
        audio_bytes = BytesIO(speech.read())
        return audio_bytes.getvalue()

# Sidebar: show story history
with st.sidebar:
    st.markdown("## 🕮 Story History")
    if st.session_state.story_history:
        for idx, story in enumerate(st.session_state.story_history, 1):
            with st.expander(f"📖 Story {idx}"):
                st.write(story)
    else:
        st.info("No stories yet. Start your first story!")

# --- Chat display ---
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(f"<div class='user-msg'>🧒 {msg['content']}</div>", unsafe_allow_html=True)
        if st.button("✏️ Edit", key=f"edit_{i}"):
            st.session_state.edit_index = i
    else:
        st.markdown(f"<div class='ai-msg'>📜 {msg['content']}</div>", unsafe_allow_html=True)
        # 🎧 Listen button for each story
        if st.button("🎧 Listen", key=f"listen_{i}"):
            audio_data = text_to_speech(msg['content'])
            st.audio(audio_data, format="audio/mp3")

st.markdown("</div>", unsafe_allow_html=True)

# --- Edit mode ---
if st.session_state.edit_index is not None:
    edit_idx = st.session_state.edit_index
    original_text = st.session_state.messages[edit_idx]["content"]
    st.markdown("### ✏️ Edit Your Previous Query")
    new_query = st.text_area("Modify your query:", original_text, key="edit_box")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Regenerate Story"):
            # Update message
            st.session_state.messages[edit_idx]["content"] = new_query
            # Remove everything after that
            st.session_state.messages = st.session_state.messages[:edit_idx + 1]

            # Build conversation
            conversation = [
                {"role": "system", "content": (
                    "You are a warm, imaginative storyteller for children. "
                    "Every response should sound like a story beginning with 'Once upon a time...' "
                    "and should be fun, educational, and easy for kids to understand."
                )}
            ] + st.session_state.messages

            # Generate story again
            new_response = generate_story(conversation)
            st.session_state.messages.append({"role": "assistant", "content": new_response})
            st.session_state.story_history.append(new_response)
            st.session_state.edit_index = None
            st.rerun()

    with col2:
        if st.button("❌ Cancel Edit"):
            st.session_state.edit_index = None
            st.rerun()

# --- Input for new queries ---
if st.session_state.edit_index is None:
    user_input = st.chat_input("Ask for a story or continue the adventure...")

    if user_input:
        # Save user input
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Full conversation
        conversation = [
            {"role": "system", "content": (
                "You are a warm, imaginative storyteller for children. "
                "Every response should sound like a story beginning with 'Once upon a time...' "
                "or 'Long ago in a faraway land...', and should be simple, fun, and educational."
                "When user asks for creating a story before that you should chat him like a human."
                "when the user don't ask to create a story format you should act like human. "
                "for example if he says 'Hello' You should interact him like a human bot create a story okay"
                "You should also follow the language in which user want to get response."
            )}
        ] + st.session_state.messages

        # Generate response
        ai_reply = generate_story(conversation)

        # Save messages and story history
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        st.session_state.story_history.append(ai_reply)

        st.rerun()

# Footer
st.markdown("---")
st.caption("Made with ❤️ using OpenAI GPT and Streamlit — A storyteller that speaks and remembers your tales 🌟")

