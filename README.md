# AI Voice Assistant - Python 3.11

A premium, feature-rich audio chatbot built with Streamlit.

## Features
- ** Voice Interaction**: Records audio with `sounddevice` and converts speech to text using Google Web STT.
- ** Premium TTS**: Supports **ElevenLabs** (High Quality AI Voice) and **gTTS** (Free).
- ** Weather**: Real-time weather updates using Open-Meteo (No API key required).
- ** Knowledge**: Answers factual questions using Wikipedia.
- ** News**: Fetches top headlines from BBC News.
- ** Jokes**: Tells random programming jokes.
- ** Modern UI**: Beautiful dark-themed interface with chat bubbles and glassmorphism.


## Setup (Windows)

1. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install dependencies:**
   ```powershell
   python -m pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

3. **Configure API Keys:**
   - Rename or create a `.env` file in the project root.
   - Add your ElevenLabs API key (optional, for premium voice):
     ```env
     ELEVENLABS_API_KEY=your_api_key_here
     ```

4. **Run the app:**
   ```powershell
   streamlit run chatbot.py
   ```

## Usage
- **Listen**: Click the "🎤 Listen" button to speak to the bot.
- **Type**: Use the text box to type messages and press Enter.
- **Commands**:
  - "Weather in [City]"
  - "Who is [Person]?"
  - "What is the news?"
  - "Tell me a joke"