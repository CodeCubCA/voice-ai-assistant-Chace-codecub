import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import sys
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
import io
from gtts import gTTS
import base64
import hashlib

# Import custom WebRTC component
from components.continuous_voice_recorder import continuous_voice_recorder

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Language configuration
LANGUAGES = {
    "English": {
        "name": "English",
        "flag": "🇺🇸",
        "code": "en",
        "speech_recognition_code": "en-US",
        "tts_code": "en"
    },
    "Spanish": {
        "name": "Spanish",
        "flag": "🇪🇸",
        "code": "es",
        "speech_recognition_code": "es-ES",
        "tts_code": "es"
    },
    "French": {
        "name": "French",
        "flag": "🇫🇷",
        "code": "fr",
        "speech_recognition_code": "fr-FR",
        "tts_code": "fr"
    },
    "Chinese": {
        "name": "Chinese (Mandarin)",
        "flag": "🇨🇳",
        "code": "zh-CN",
        "speech_recognition_code": "zh-CN",
        "tts_code": "zh-CN"
    },
    "Japanese": {
        "name": "Japanese",
        "flag": "🇯🇵",
        "code": "ja",
        "speech_recognition_code": "ja-JP",
        "tts_code": "ja"
    }
}

# Personality system prompts
PERSONALITIES = {
    "General Assistant": {
        "name": "General Assistant",
        "description": "A helpful AI assistant for general queries",
        "system_prompt": "You are a helpful, friendly, and knowledgeable AI assistant. Provide clear, accurate, and helpful responses to user questions."
    },
    "Study Buddy": {
        "name": "Study Buddy",
        "description": "Your friendly learning companion",
        "system_prompt": "You are a patient and encouraging study buddy. Help users learn by explaining concepts clearly, breaking down complex topics, providing examples, and encouraging questions. Be supportive and enthusiastic about learning."
    },
    "Fitness Coach": {
        "name": "Fitness Coach",
        "description": "Your personal fitness and wellness guide",
        "system_prompt": "You are an energetic and motivating fitness coach. Provide workout advice, nutrition tips, and encouragement. Be positive, supportive, and focus on healthy, sustainable fitness practices. Always remind users to consult healthcare professionals for medical advice."
    },
    "Gaming Helper": {
        "name": "Gaming Helper",
        "description": "Your gaming tips and tricks companion",
        "system_prompt": "You are an enthusiastic gaming expert. Help users with game strategies, tips, recommendations, and gaming-related questions. Be fun, engaging, and knowledgeable about various gaming platforms and genres."
    }
}

# Page configuration
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Scroll to last AI response or voice input section
import streamlit.components.v1 as components

# Determine scroll target based on conversation flow mode
scroll_target = "voice_input" if st.session_state.get("show_continue_prompt", False) else "assistant"

components.html(
    f"""
    <script>
        function scrollToTarget() {{
            setTimeout(() => {{
                const target = '{scroll_target}';

                if (target === 'voice_input') {{
                    // Scroll to voice input section
                    const voiceSection = window.parent.document.evaluate(
                        "//h3[contains(text(), 'Voice Input')]",
                        window.parent.document,
                        null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE,
                        null
                    ).singleNodeValue;

                    if (voiceSection) {{
                        voiceSection.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }}
                }} else {{
                    // Scroll to last assistant message
                    const messages = window.parent.document.querySelectorAll('[data-testid="stChatMessage"]');
                    let lastAssistant = null;

                    for (let i = messages.length - 1; i >= 0; i--) {{
                        if (messages[i].querySelector('[data-testid="chatAvatarIcon-assistant"]')) {{
                            lastAssistant = messages[i];
                            break;
                        }}
                    }}

                    if (lastAssistant) {{
                        lastAssistant.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    }}
                }}
            }}, 300);
        }}

        scrollToTarget();
        window.addEventListener('load', scrollToTarget);
    </script>
    """,
    height=0,
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "personality" not in st.session_state:
    st.session_state.personality = "General Assistant"

if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

if "auto_send_voice" not in st.session_state:
    st.session_state.auto_send_voice = False

if "show_edit" not in st.session_state:
    st.session_state.show_edit = False

if "enable_voice_response" not in st.session_state:
    st.session_state.enable_voice_response = False

if "tts_audio" not in st.session_state:
    st.session_state.tts_audio = {}

if "processing" not in st.session_state:
    st.session_state.processing = False

if "language" not in st.session_state:
    st.session_state.language = "English"

if "last_language" not in st.session_state:
    st.session_state.last_language = "English"

if "conversation_flow_mode" not in st.session_state:
    st.session_state.conversation_flow_mode = False

if "conversation_turns" not in st.session_state:
    st.session_state.conversation_turns = 0

if "show_continue_prompt" not in st.session_state:
    st.session_state.show_continue_prompt = False

if "automatic_mode" not in st.session_state:
    st.session_state.automatic_mode = False

if "auto_record_trigger" not in st.session_state:
    st.session_state.auto_record_trigger = 0

# Function to clean text for TTS
def clean_text_for_speech(text):
    """Remove unnecessary symbols and clean text for natural speech"""
    import re

    # Remove markdown formatting
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold **text**
    text = re.sub(r'\*(.+?)\*', r'\1', text)  # Italic *text*
    text = re.sub(r'__(.+?)__', r'\1', text)  # Bold __text__
    text = re.sub(r'_(.+?)_', r'\1', text)  # Italic _text_
    text = re.sub(r'`(.+?)`', r'\1', text)  # Code `text`
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Code blocks

    # Remove markdown links but keep text: [text](url) -> text
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)

    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

    # Remove bullet points and list markers
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Remove extra symbols that don't add to speech
    text = re.sub(r'[#|>]', '', text)

    # Clean up multiple spaces and newlines
    text = re.sub(r'\n+', '. ', text)
    text = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text

# Function to generate TTS audio
def generate_tts_audio(text, message_index, tts_lang_code):
    """Generate audio from text using gTTS and store in session state"""
    try:
        # Create a unique key for this message including language
        audio_key = f"audio_{message_index}_{tts_lang_code}"

        # Only generate if not already generated
        if audio_key not in st.session_state.tts_audio:
            # Clean text for better speech
            clean_text = clean_text_for_speech(text)

            # Warn for very long messages
            if len(clean_text) > 500:
                with st.spinner("🎵 Generating audio for long message..."):
                    # Truncate extremely long messages for TTS
                    tts_text = clean_text[:1000] + "..." if len(clean_text) > 1000 else clean_text

                    # Generate speech with selected language
                    tts = gTTS(text=tts_text, lang=tts_lang_code, slow=False)

                    # Save to bytes
                    audio_bytes = io.BytesIO()
                    tts.write_to_fp(audio_bytes)
                    audio_bytes.seek(0)

                    # Store in session state
                    st.session_state.tts_audio[audio_key] = audio_bytes.read()
            else:
                # Generate speech for normal messages with selected language
                tts = gTTS(text=clean_text, lang=tts_lang_code, slow=False)

                # Save to bytes
                audio_bytes = io.BytesIO()
                tts.write_to_fp(audio_bytes)
                audio_bytes.seek(0)

                # Store in session state
                st.session_state.tts_audio[audio_key] = audio_bytes.read()

        return st.session_state.tts_audio[audio_key]
    except Exception as e:
        st.error(f"❌ Audio generation failed: {str(e)}")
        return None

# Function to transcribe audio to text
def transcribe_audio(audio_bytes, language_code):
    """Convert audio bytes to text using speech recognition"""
    try:
        # Initialize recognizer with optimized settings
        recognizer = sr.Recognizer()

        # Adjust energy threshold for better recognition
        recognizer.energy_threshold = 200  # Lower threshold for quieter speech
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8  # Shorter pause detection

        # Save audio bytes to a temporary WAV file for better compatibility
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name

        # Load audio file using speech_recognition
        with sr.AudioFile(temp_audio_path) as source:
            # Adjust for ambient noise with longer duration for better accuracy
            recognizer.adjust_for_ambient_noise(source, duration=0.3)

            # Record the audio
            audio_data = recognizer.record(source)

        # Clean up temporary file
        import os
        os.unlink(temp_audio_path)

        # Try to recognize speech with show_all=True to get alternatives
        try:
            # Get detailed results with confidence scores using the selected language
            result = recognizer.recognize_google(audio_data, language=language_code, show_all=True)

            if result and len(result['alternative']) > 0:
                # Return the best transcription (first alternative has highest confidence)
                text = result['alternative'][0]['transcript']
                return text
            else:
                return "[unclear audio - could not transcribe]"

        except:
            # Fallback to simple recognition with selected language
            text = recognizer.recognize_google(audio_data, language=language_code)
            return text

    except sr.UnknownValueError:
        # Return a placeholder that allows editing instead of an error
        return "[unclear audio - please edit]"
    except sr.RequestError as e:
        return f"[Error: {e}]"
    except Exception as e:
        return f"[Error: {str(e)}]"

# Sidebar
with st.sidebar:
    st.title("🤖 AI Chatbot Settings")
    st.markdown("---")

    # Language selector
    st.subheader("🌍 Language")

    # Create language options with flags
    language_options = [f"{LANGUAGES[lang]['flag']} {LANGUAGES[lang]['name']}" for lang in LANGUAGES.keys()]
    language_keys = list(LANGUAGES.keys())

    selected_language_display = st.selectbox(
        "Select Language:",
        options=language_options,
        index=language_keys.index(st.session_state.language)
    )

    # Extract the actual language key from the display string
    selected_language = language_keys[language_options.index(selected_language_display)]

    # Update language if changed
    if selected_language != st.session_state.language:
        st.session_state.last_language = st.session_state.language
        st.session_state.language = selected_language
        # Clear TTS audio cache when language changes
        st.session_state.tts_audio = {}
        st.rerun()

    # Also update last_language if they match (for tracking)
    if st.session_state.language != st.session_state.last_language:
        st.session_state.tts_audio = {}
        st.session_state.last_language = st.session_state.language

    # Display current language info
    current_lang = LANGUAGES[st.session_state.language]
    st.info(f"🗣️ **Current:** {current_lang['flag']} {current_lang['name']}")

    st.markdown("---")

    # Personality selector
    st.subheader("Choose Personality")
    selected_personality = st.selectbox(
        "Select AI Personality:",
        options=list(PERSONALITIES.keys()),
        index=list(PERSONALITIES.keys()).index(st.session_state.personality)
    )

    # Update personality if changed
    if selected_personality != st.session_state.personality:
        st.session_state.personality = selected_personality
        st.session_state.messages = []  # Clear chat history on personality change
        st.rerun()

    # Display personality info
    st.markdown("---")
    st.subheader("Current Assistant")
    current_personality = PERSONALITIES[st.session_state.personality]
    st.write(f"**{current_personality['name']}**")
    st.write(current_personality['description'])

    st.markdown("---")
    st.subheader("About")
    st.write("This chatbot uses Google's Gemini 2.5 Flash model to provide intelligent responses.")

    # Clear chat button
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    with st.expander("🔊 Voice Settings", expanded=True):
        st.session_state.enable_voice_response = st.checkbox(
            "Enable AI voice responses",
            value=st.session_state.enable_voice_response,
            help="AI will speak responses aloud with audio players below each message"
        )
        if st.session_state.enable_voice_response:
            st.info("💡 Tip: Audio players will appear below AI responses. Click play to listen!")

        st.markdown("---")

        st.session_state.conversation_flow_mode = st.checkbox(
            "🔄 Enhanced Conversation Flow (Semi-Automatic)",
            value=st.session_state.conversation_flow_mode and not st.session_state.automatic_mode,
            disabled=st.session_state.automatic_mode,
            help="After AI responds, show a prominent prompt to continue talking"
        )

        st.markdown("---")

        # Enable automatic mode with WebRTC component
        st.session_state.automatic_mode = st.checkbox(
            "🤖 Fully Automatic Mode (WebRTC)",
            value=st.session_state.automatic_mode,
            disabled=st.session_state.conversation_flow_mode,
            help="Automatically starts recording after AI responds. Uses Voice Activity Detection to detect when you stop speaking."
        )

        st.info("💡 **Tip:** Use Enhanced Conversation Flow for faster multi-turn conversations, or enable Fully Automatic Mode for hands-free operation!")

        if st.session_state.conversation_flow_mode:
            st.success("✅ Flow mode active - conversation prompts enabled!")
            if st.session_state.conversation_turns > 0:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.metric("Conversation Turns", st.session_state.conversation_turns)
                with col2:
                    if st.button("Reset", key="reset_turns"):
                        st.session_state.conversation_turns = 0
                        st.session_state.show_continue_prompt = False
                        st.rerun()
        elif st.session_state.automatic_mode:
            st.success("✅ Automatic mode active - hands-free conversation enabled!")
            st.info("🎙️ The microphone will automatically start after AI responds and stop when you finish speaking (2 seconds of silence).")
            if st.session_state.conversation_turns > 0:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.metric("Conversation Turns", st.session_state.conversation_turns)
                with col2:
                    if st.button("Reset", key="reset_auto_turns"):
                        st.session_state.conversation_turns = 0
                        st.session_state.auto_record_trigger = 0
                        st.rerun()

# Main chat interface
st.title(f"💬 Chat with {PERSONALITIES[st.session_state.personality]['name']}")

# Display chat messages
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

    # Display audio player OUTSIDE chat message for assistant responses
    if message["role"] == "assistant" and st.session_state.enable_voice_response:
        # Add subtle divider for visual separation
        st.markdown("---")

        # Use columns for better layout (responsive on mobile)
        col1, col2 = st.columns([4, 1])

        with col1:
            # Get TTS language code for the selected language
            tts_lang_code = LANGUAGES[st.session_state.language]['tts_code']

            audio_data = generate_tts_audio(message["content"], idx, tts_lang_code)
            if audio_data:
                lang_info = LANGUAGES[st.session_state.language]
                st.markdown(f"🔊 **Listen to response** ({lang_info['flag']} {lang_info['name']}):")
                st.audio(audio_data, format="audio/mp3")

                # Show truncation warning if message was too long
                if len(message["content"]) > 1000:
                    st.caption("⚠️ Audio truncated to first 1000 characters")
            else:
                st.error("❌ Could not generate audio. Please try refreshing the page.")

        with col2:
            # Empty column for spacing (adjusts automatically on mobile)
            pass

        st.markdown("")  # Add spacing after audio section

# Voice Input Section
st.markdown("### 🎤 Voice Input")

# Show different prompts based on mode
if st.session_state.automatic_mode and len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "assistant":
    st.info("🤖 **Automatic mode active** - Recording will start automatically below...")
    st.markdown("---")
elif st.session_state.show_continue_prompt and st.session_state.conversation_flow_mode:
    st.success("### 🎙️ **Ready to continue? Click the microphone below!**")
    st.info(f"💬 Conversation turn #{st.session_state.conversation_turns + 1} - Keep the conversation going!")

    # Add a dismiss button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("✓ Got it", type="secondary"):
            st.session_state.show_continue_prompt = False
            st.rerun()

    st.markdown("---")

with st.expander("ℹ️ How to use voice input", expanded=False):
    st.markdown("""
    **Manual Mode (Default):**
    1. Select your preferred language in the sidebar (🌍 Language)
    2. Click the microphone button below
    3. Speak your message clearly in the selected language
    4. Click stop when finished
    5. Message will auto-send after 1 second

    **🔄 Enhanced Conversation Flow (Semi-Automatic):**
    - Enable in Voice Settings sidebar
    - After AI responds, you'll see a prominent "Continue" prompt
    - Page automatically scrolls to microphone
    - Track conversation turns in the sidebar
    - Makes multi-turn conversations much faster!

    **🤖 Fully Automatic Mode (Hands-Free):**
    - Enable "Fully Automatic Mode" in Voice Settings
    - Microphone automatically starts after AI responds
    - Uses Voice Activity Detection (VAD) to detect when you stop speaking
    - Automatically stops after 2 seconds of silence
    - Perfect for hands-free, natural conversations!
    - Note: Only one mode can be active at a time

    **Tips:**
    - Speak clearly and at a normal pace
    - Minimize background noise for best results
    - You can edit transcriptions if needed
    - AI will respond in your selected language

    **Supported Languages:**
    🇺🇸 English | 🇪🇸 Spanish | 🇫🇷 French | 🇨🇳 Chinese | 🇯🇵 Japanese
    """)

# Show edit option BEFORE the audio recorder
if st.session_state.show_edit and st.session_state.voice_text and len(st.session_state.messages) > 0:
    if st.session_state.messages[-2]["content"] == st.session_state.voice_text if len(st.session_state.messages) >= 2 else False:
        with st.expander("📝 Edit Last Voice Message", expanded=True):
            edited_text = st.text_area(
                "Edit and resend:",
                value=st.session_state.voice_text,
                height=80,
                key="voice_edit_area"
            )

            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("Resend", type="primary", key="resend_voice"):
                    st.session_state.messages = st.session_state.messages[:-2]
                    st.session_state.messages.append({"role": "user", "content": edited_text})
                    st.session_state.voice_text = ""
                    st.session_state.show_edit = False
                    st.rerun()
            with col2:
                if st.button("Clear", key="clear_edit"):
                    st.session_state.voice_text = ""
                    st.session_state.show_edit = False
                    st.rerun()

# Audio recorder - use different component based on mode
audio_bytes = None

if st.session_state.automatic_mode:
    # Use continuous WebRTC recorder with Voice Activity Detection
    # Auto-start if this is after an AI response
    should_auto_start = len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "assistant"

    audio_data = continuous_voice_recorder(
        auto_start=should_auto_start,
        silence_threshold=0.02,
        silence_duration=2.0,
        key=f"auto_recorder_{st.session_state.auto_record_trigger}"
    )

    # Convert base64 data URL to bytes if audio was received
    if audio_data and 'audio' in audio_data:
        import base64
        import re
        # Extract base64 data from data URL
        match = re.match(r'data:audio/(\w+);base64,(.+)', audio_data['audio'])
        if match:
            audio_base64 = match.group(2)
            audio_bytes = base64.b64decode(audio_base64)

else:
    # Use manual audio recorder
    audio_bytes = audio_recorder(
        text="Click to record",
        recording_color="#e74c3c",
        neutral_color="#3498db",
        icon_name="microphone",
        icon_size="2x",
    )

# Process recorded audio and auto-send
if audio_bytes:
    # Create a hash of the audio to detect new recordings
    import hashlib
    audio_hash = hashlib.md5(audio_bytes).hexdigest()

    # Only process if this is a new recording
    if audio_hash != st.session_state.last_audio_hash:
        # Hide edit section when microphone is touched
        st.session_state.show_edit = False
        # Clear previous edit text when starting new recording
        st.session_state.voice_text = ""
        # Hide continue prompt when user starts speaking
        st.session_state.show_continue_prompt = False

        st.session_state.last_audio_hash = audio_hash

        st.audio(audio_bytes, format="audio/wav")

        # Get the speech recognition code for the selected language
        lang_config = LANGUAGES[st.session_state.language]
        speech_lang_code = lang_config['speech_recognition_code']

        with st.spinner(f"Transcribing your voice ({lang_config['flag']} {lang_config['name']})..."):
            transcribed_text = transcribe_audio(audio_bytes, speech_lang_code)

        st.success(f"Transcribed: {transcribed_text}")

        # Auto-send after 1 second
        import time
        countdown_placeholder = st.empty()
        countdown_placeholder.info("Sending in 1 second...")
        time.sleep(1)
        countdown_placeholder.empty()

        # Auto-send the message
        prompt = transcribed_text

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Get current personality system prompt
                    base_system_prompt = PERSONALITIES[st.session_state.personality]["system_prompt"]

                    # Add language instruction to system prompt
                    lang_name = LANGUAGES[st.session_state.language]["name"]
                    if st.session_state.language != "English":
                        system_prompt = f"{base_system_prompt}\n\nIMPORTANT: Please respond in {lang_name}. The user is communicating in {lang_name}, so respond naturally in {lang_name}."
                    else:
                        system_prompt = base_system_prompt

                    # Initialize model with system instruction
                    model = genai.GenerativeModel(
                        'gemini-2.5-flash',
                        system_instruction=system_prompt
                    )

                    # Build conversation history for context
                    chat_history = []
                    for msg in st.session_state.messages[:-1]:
                        # Convert 'assistant' role to 'model' for Gemini API
                        role = "model" if msg["role"] == "assistant" else msg["role"]
                        chat_history.append({
                            "role": role,
                            "parts": [msg["content"]]
                        })

                    # Start chat with history
                    chat = model.start_chat(history=chat_history)

                    # Send message and get response
                    response = chat.send_message(prompt)
                    assistant_response = response.text

                    # Display response
                    st.markdown(assistant_response)

                    # Add assistant response to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response
                    })

                    # Store the transcription for editing after response
                    st.session_state.voice_text = transcribed_text
                    # Show edit section after response is received
                    st.session_state.show_edit = True

                    # If conversation flow mode is enabled, show continue prompt
                    if st.session_state.conversation_flow_mode:
                        st.session_state.show_continue_prompt = True
                        st.session_state.conversation_turns += 1

                    # If automatic mode is enabled, increment trigger to restart recorder
                    if st.session_state.automatic_mode:
                        st.session_state.auto_record_trigger += 1
                        st.session_state.conversation_turns += 1

                except Exception as e:
                    error_message = f"Error: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message
                    })

        st.rerun()

st.markdown("---")

# Chat input
if prompt := st.chat_input("Type your message here or use voice input above..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Get current personality system prompt
                base_system_prompt = PERSONALITIES[st.session_state.personality]["system_prompt"]

                # Add language instruction to system prompt
                lang_name = LANGUAGES[st.session_state.language]["name"]
                if st.session_state.language != "English":
                    system_prompt = f"{base_system_prompt}\n\nIMPORTANT: Please respond in {lang_name}. The user is communicating in {lang_name}, so respond naturally in {lang_name}."
                else:
                    system_prompt = base_system_prompt

                # Initialize model with system instruction
                model = genai.GenerativeModel(
                    'gemini-2.5-flash',
                    system_instruction=system_prompt
                )

                # Build conversation history for context
                chat_history = []
                for msg in st.session_state.messages[:-1]:  # Exclude the last user message we just added
                    # Convert 'assistant' role to 'model' for Gemini API
                    role = "model" if msg["role"] == "assistant" else msg["role"]
                    chat_history.append({
                        "role": role,
                        "parts": [msg["content"]]
                    })

                # Start chat with history
                chat = model.start_chat(history=chat_history)

                # Send message and get response
                response = chat.send_message(prompt)
                assistant_response = response.text

                # Display response
                st.markdown(assistant_response)

                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_response
                })

            except Exception as e:
                error_message = f"Error: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message
                })

# Footer
st.markdown("---")
st.markdown("*Powered by Google Gemini 2.5 Flash | Built with Streamlit*")
