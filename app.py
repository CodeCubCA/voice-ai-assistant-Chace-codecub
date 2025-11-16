import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
import io
import pyttsx3
import base64
import threading

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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

# Scroll to last AI response
import streamlit.components.v1 as components
components.html(
    """
    <script>
        function scrollToLastAssistantMessage() {
            setTimeout(() => {
                const messages = window.parent.document.querySelectorAll('[data-testid="stChatMessage"]');
                let lastAssistant = null;

                for (let i = messages.length - 1; i >= 0; i--) {
                    if (messages[i].querySelector('[data-testid="chatAvatarIcon-assistant"]')) {
                        lastAssistant = messages[i];
                        break;
                    }
                }

                if (lastAssistant) {
                    lastAssistant.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 300);
        }

        scrollToLastAssistantMessage();
        window.addEventListener('load', scrollToLastAssistantMessage);
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

if "speech_engine" not in st.session_state:
    st.session_state.speech_engine = None

# Function to stop any ongoing speech
def stop_speech():
    """Stop any currently running speech"""
    try:
        if st.session_state.speech_engine is not None:
            st.session_state.speech_engine.stop()
    except:
        pass

# Function to speak text directly (no file needed)
def speak_text(text):
    """Speak text using pyttsx3 (offline, much faster)"""
    try:
        # Initialize pyttsx3 engine
        engine = pyttsx3.init()

        # Store engine in session state so we can stop it later
        st.session_state.speech_engine = engine

        # Set properties for more natural-sounding voice
        voices = engine.getProperty('voices')

        # Use ONLY female voice (Samantha on macOS)
        # Find Samantha specifically by name, or any female voice
        female_voice = None
        for voice in voices:
            voice_name = voice.name.lower()
            # Look for Samantha or any female voice identifier
            if 'samantha' in voice_name or 'female' in voice_name or 'woman' in voice_name:
                female_voice = voice.id
                break

        # If no explicitly female voice found, use index 1 (typically female on macOS)
        if female_voice:
            engine.setProperty('voice', female_voice)
        elif len(voices) > 1:
            # Force use of second voice which is typically female (Samantha)
            engine.setProperty('voice', voices[1].id)
        else:
            # Last resort fallback
            engine.setProperty('voice', voices[0].id)

        # Set speech rate (faster for quicker responses)
        engine.setProperty('rate', 190)

        # Set volume (0.0 to 1.0)
        engine.setProperty('volume', 0.9)

        # Speak the text
        engine.say(text)
        engine.runAndWait()

        # Clear engine from session state after speaking
        st.session_state.speech_engine = None

        return True
    except Exception as e:
        st.session_state.speech_engine = None
        st.error(f"Error generating speech: {str(e)}")
        return False

# Function to transcribe audio to text
def transcribe_audio(audio_bytes):
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
            # Get detailed results with confidence scores
            result = recognizer.recognize_google(audio_data, language="en-US", show_all=True)

            if result and len(result['alternative']) > 0:
                # Return the best transcription (first alternative has highest confidence)
                text = result['alternative'][0]['transcript']
                return text
            else:
                return "[unclear audio - could not transcribe]"

        except:
            # Fallback to simple recognition
            text = recognizer.recognize_google(audio_data, language="en-US")
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
    st.subheader("Voice Response")
    st.session_state.enable_voice_response = st.checkbox(
        "Enable AI voice responses",
        value=st.session_state.enable_voice_response,
        help="AI will speak responses aloud in addition to showing text"
    )

# Main chat interface
st.title(f"💬 Chat with {PERSONALITIES[st.session_state.personality]['name']}")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Voice Input Section
st.markdown("### 🎤 Voice Input")
st.info("Click the microphone button, speak your message, then click stop. The message will auto-send after 1 second.")

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

# Audio recorder
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
        # Stop any ongoing speech when microphone is clicked
        stop_speech()

        # Hide edit section when microphone is touched
        st.session_state.show_edit = False
        # Clear previous edit text when starting new recording
        st.session_state.voice_text = ""

        st.session_state.last_audio_hash = audio_hash

        st.audio(audio_bytes, format="audio/wav")

        with st.spinner("Transcribing your voice..."):
            transcribed_text = transcribe_audio(audio_bytes)

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
                    system_prompt = PERSONALITIES[st.session_state.personality]["system_prompt"]

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

                    # Text-to-speech for AI response
                    if st.session_state.enable_voice_response:
                        # Speak in a separate thread so it doesn't block the UI
                        import threading
                        speech_thread = threading.Thread(target=speak_text, args=(assistant_response,))
                        speech_thread.start()

                    # Add assistant response to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response
                    })

                    # Store the transcription for editing after response
                    st.session_state.voice_text = transcribed_text
                    # Show edit section after response is received
                    st.session_state.show_edit = True

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
                system_prompt = PERSONALITIES[st.session_state.personality]["system_prompt"]

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

                # Text-to-speech for AI response
                if st.session_state.enable_voice_response:
                    # Speak in a separate thread so it doesn't block the UI
                    import threading
                    speech_thread = threading.Thread(target=speak_text, args=(assistant_response,))
                    speech_thread.start()

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
