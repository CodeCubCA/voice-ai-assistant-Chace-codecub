---
title: Voice AI Assistant
emoji: 🎤
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: "1.31.0"
app_file: app.py
pinned: false
---

# Voice AI Assistant

An intelligent AI chatbot with advanced voice input and output capabilities, powered by Google Gemini AI. This application provides a seamless conversational experience with multi-language support and customizable AI personalities.

## Screenshots

### Main Interface
![Main Interface](screenshots/main-interface.png)
*The Voice AI Assistant main interface showing the chat area, voice input controls, and sidebar settings*

### Voice Input Modes
![Voice Input](screenshots/voice-input.png)
*Three voice input modes: Manual Recording, Enhanced Conversation Flow, and Fully Automatic Mode*

### Multi-Language Support
![Language Selection](screenshots/language-selection.png)
*Support for 5 languages: English, Spanish, French, Chinese (Mandarin), and Japanese*

### AI Personalities
![AI Personalities](screenshots/personalities.png)
*Choose from 4 different AI personalities: General Assistant, Study Buddy, Creative Writer, and Tech Expert*

### Enhanced Conversation Flow
![Conversation Flow](screenshots/conversation-flow.png)
*Semi-automatic conversation mode with turn tracking and auto-scroll to latest responses*

## Features

### Core Capabilities
- **Voice Input**: Record your voice directly in the browser using the Web Speech API
- **Voice Output**: AI responses are spoken aloud using Google Text-to-Speech (gTTS)
- **Multi-Language Support**: Communicate in 5 languages:
  - 🇺🇸 English
  - 🇪🇸 Spanish
  - 🇫🇷 French
  - 🇨🇳 Chinese (Mandarin)
  - 🇯🇵 Japanese
- **AI Conversation**: Powered by Google Gemini 2.5 Flash for intelligent, context-aware responses
- **Multiple Personalities**: Choose from 4 different AI personalities:
  - General Assistant
  - Study Buddy
  - Creative Writer
  - Tech Expert

### Enhanced Features
- **Automatic Speech Recognition**: Transcribes voice input automatically with editable results
- **Auto-Send**: Messages automatically send after 1 second of transcription
- **Enhanced Conversation Flow**: Semi-automatic conversation mode with turn tracking
- **Smart Text Cleaning**: Removes markdown symbols from TTS output for natural speech
- **Session Persistence**: Maintains conversation history throughout your session
- **Audio Caching**: Efficient audio generation and caching for faster playback
- **Responsive UI**: Polished interface with auto-scroll to latest responses
- **Edit Transcriptions**: Modify voice transcriptions before sending if needed

## Technologies Used

### Backend
- **Python 3.8+**: Core programming language
- **Streamlit**: Web application framework for the user interface
- **Google Generative AI (Gemini 2.5 Flash)**: AI model for intelligent conversations
- **gTTS (Google Text-to-Speech)**: Multi-language text-to-speech synthesis
- **SpeechRecognition**: Google Speech Recognition API for voice-to-text

### Frontend
- **Streamlit Components**: Interactive UI elements
- **audio-recorder-streamlit**: Browser-based audio recording
- **Web Speech API**: Browser voice input capabilities
- **JavaScript**: Custom auto-scroll functionality

### Additional Libraries
- **python-dotenv**: Environment variable management
- **pydub**: Audio processing utilities

## Requirements

- Python 3.8 or higher
- Google Gemini API key
- Internet connection (required for Speech Recognition and TTS)
- Modern web browser with microphone access

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd "Voice AI-Assistant"
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

The required packages are:
```
streamlit>=1.31.0
google-generativeai>=0.3.2
python-dotenv>=1.0.0
audio-recorder-streamlit>=0.0.8
SpeechRecognition>=3.10.0
pydub>=0.25.1
gTTS>=2.3.2
pyttsx3>=2.90
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root directory:

```bash
# Copy the example file
cp .env.example .env
```

Edit the `.env` file and add your Google Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

**How to get a Gemini API key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste it into your `.env` file

### 4. Run the Application

```bash
streamlit run app.py
```

The application will open automatically in your default browser at `http://localhost:8501`

## Usage Guide

### Getting Started

1. **Launch the Application**: Run `streamlit run app.py`
2. **Select Language**: Choose your preferred language from the sidebar (🌍 Language)
3. **Choose Personality**: Select an AI personality that fits your needs
4. **Enable Voice Response**: Toggle "Enable AI voice responses" in the Voice Settings

### Using Voice Input

1. Click the microphone button in the Voice Input section
2. Speak clearly in your selected language
3. Click stop when finished speaking
4. The transcription will appear automatically
5. Message auto-sends after 1 second
6. Edit the transcription if needed (edit option appears after AI response)

### Enhanced Conversation Flow

For faster multi-turn conversations:

1. Enable "🔄 Enhanced Conversation Flow" in the Voice Settings sidebar
2. After the AI responds, you'll see a prominent "Ready to continue?" prompt
3. The page automatically scrolls to highlight the microphone
4. Track your conversation turns in the sidebar
5. Continue speaking to maintain the conversation flow

### Text Input

You can also type messages directly in the chat input at the bottom of the page for text-based conversation.

### Tips for Best Results

- **Speak clearly** at a normal pace
- **Minimize background noise** for accurate transcription
- **Use headphones** to prevent audio feedback during voice responses
- **Edit transcriptions** if the speech recognition makes mistakes
- **Switch languages** anytime from the sidebar
- **Try different personalities** to find the best fit for your task

## 🚀 Live Deployments

This project is deployed on multiple platforms for easy access:

- **Render**: [https://voice-ai-assistant-l8hg.onrender.com/](https://voice-ai-assistant-l8hg.onrender.com/)
- **Hugging Face Spaces**: [https://huggingface.co/spaces/Chace-codecub/Voice-AI-Assistant](https://huggingface.co/spaces/Chace-codecub/Voice-AI-Assistant)

You can try the live application without any local setup by visiting either of these links.

## Project Structure

```
Voice AI-Assistant/
├── app.py                          # Main application file
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (API keys)
├── .env.example                   # Template for environment variables
├── .gitignore                     # Git ignore rules
├── README.md                      # This file
└── components/                    # Custom Streamlit components
    └── continuous_voice_recorder/ # WebRTC voice recorder (in development)
```

## Features in Development

- **Fully Automatic Continuous Conversation**: Custom WebRTC component for automatic voice recording without manual button clicks
- **Advanced Voice Activity Detection (VAD)**: Intelligent silence detection for natural conversation flow

## Troubleshooting

### Microphone Not Working
- Ensure your browser has microphone permissions enabled
- Check that no other application is using the microphone
- Try refreshing the page

### API Errors
- Verify your Gemini API key is correctly set in the `.env` file
- Check your internet connection
- Ensure your API key has not exceeded its quota

### Audio Not Playing
- Enable voice responses in the Voice Settings sidebar
- Check your browser audio settings
- Ensure speakers/headphones are connected and working

### Language Switching Issues
- If audio doesn't match the selected language, refresh the page
- Audio cache automatically clears when switching languages

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is open source and available for educational and personal use.

## Acknowledgments

- Powered by [Google Gemini AI](https://deepmind.google/technologies/gemini/)
- Built with [Streamlit](https://streamlit.io/)
- Voice synthesis by [gTTS](https://github.com/pndurette/gTTS)
- Speech recognition by [Google Speech Recognition API](https://cloud.google.com/speech-to-text)

---

**Powered by Google Gemini 2.5 Flash | Built with Streamlit**
