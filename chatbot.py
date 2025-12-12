import streamlit as st
import streamlit as st
import time, io, os, sys, re
from gtts import gTTS
import numpy as np
from dotenv import load_dotenv
import feedparser
import pyjokes
import ast
import math


load_dotenv()

# audio libs
try:
    import sounddevice as sd
    import soundfile as sf
except Exception:
    sd = None
    sf = None

try:
    import speech_recognition as sr
except Exception:
    sr = None

try:
    import noisereduce as nr
except Exception:
    nr = None

import requests
import wikipedia

# Config
RECORD_DURATION = 5.0   # seconds
SAMPLERATE = 16000
CHANNELS = 1
USE_NOISE_REDUCTION = True if nr is not None else False
TTS_LANG = "en"

st.set_page_config(page_title="AI Voice Assistant", layout="wide", page_icon="🎙️")

# CSS
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background: linear-gradient(to right, #141e30, #243b55);
        color: white;
    }

    /* Force all common text elements to be white */
    p, label, h1, h2, h3, h4, h5, h6, .stMarkdown, .stCaption, li, .stText {
        color: #ffffff !important;
    }

    /* Buttons */
    .stButton>button, div[data-testid="stFormSubmitButton"]>button {
        background: linear-gradient(45deg, #FF512F, #DD2476) !important;
        color: white !important;
        border: none;
        border-radius: 25px;
        padding: 10px 24px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover, div[data-testid="stFormSubmitButton"]>button:hover {
        transform: scale(1.05);
        box_shadow: 0 5px 15px rgba(221, 36, 118, 0.4);
        color: white !important;
    }

    /* Input Fields */
    .stTextInput>div>div>input {
        border-radius: 20px;
        border: 2px solid #DD2476;
        background-color: rgba(255, 255, 255, 0.1);
        color: black !important;
        caret-color: black;
    }
    
    /* Title Styling */
    h1 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        background: -webkit-linear-gradient(#ffffff, #a8c0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Chat Bubbles */
    .chat-message {
        padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
    }
    .chat-message.user {
        background-color: rgba(255, 255, 255, 0.1);
        border-left: 5px solid #FF512F;
    }
    .chat-message.bot {
        background-color: rgba(0, 0, 0, 0.2);
        border-left: 5px solid #DD2476;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #334155;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title(" AI Voice Assistant")
st.markdown("### *Your intelligent companion for Weather, Knowledge, News, and Fun.*")

st.sidebar.header("Settings")
record_dur = st.sidebar.slider("Record duration (secs)", 2.0, 8.0, RECORD_DURATION, 0.5)
st.sidebar.write("Sample rate:", SAMPLERATE)

# TTS Settings
# TTS Settings
st.sidebar.subheader("Text-to-Speech")
tts_provider = st.sidebar.radio("TTS Provider", ["ElevenLabs (Premium)","gTTS (Free)"])

if tts_provider == "ElevenLabs (Premium)":
    if not os.getenv("ELEVENLABS_API_KEY"):
        st.sidebar.warning(" Please set ELEVENLABS_API_KEY in your .env file")

if st.sidebar.button("Clear Conversation"):
    st.session_state["history"] = []
    st.rerun()

st.sidebar.write("---")
st.sidebar.write("Note: gTTS and Google STT require internet. Open-Meteo and Wikipedia are free APIs.")
st.sidebar.write("---")

col1, col2 = st.columns([1,2])
with col1:
    listen_btn = st.button(" Listen (record)")
    with st.form(key='chat_form', clear_on_submit=True):
        typed = st.text_input("Or type message", key="user_input")
        send_btn = st.form_submit_button("Send Text")
    st.write("Tools: Wikipedia (knowledge), Open-Meteo (weather), BBC (News), Pyjokes (Jokes)")

with col2:
    st.header("")
    if "history" not in st.session_state:
        st.session_state["history"] = []
status = st.empty()

# Helpers

def tts_bytes(text: str, lang=TTS_LANG):
    """
    Generate audio bytes for the given text using the selected provider.
    """
    if tts_provider == "ElevenLabs (Premium)":
        api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
        if not api_key or api_key == "your_api_key_here":
            st.error("⚠️ ElevenLabs API Key is missing or invalid in .env file.")
            return None
        return tts_elevenlabs(text, api_key)
    else:
        # Fallback to gTTS
        try:
            t = gTTS(text=text, lang=lang)
            buf = io.BytesIO()
            t.write_to_fp(buf)
            buf.seek(0)
            return buf.read()
        except Exception as e:
            print("[tts_bytes] Exception:", e)
            return None

def tts_elevenlabs(text, api_key, voice_id="21m00Tcm4TlvDq8ikWAM"): # Rachel voice
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 401:
            st.error(" ElevenLabs Error: Unauthorized (401).")
            st.error(f"Server Message: {response.text}")
            
        response.raise_for_status()
        return response.content
    except Exception as e:
        st.error(f"ElevenLabs TTS Error: {e}")
        return None

def recognize_from_bytes(wav_bytes, samplerate=SAMPLERATE, sample_width=2, show_debug=True):
    
    if sr is None:
        return False, "speech_recognition not installed"

    try:
        if show_debug:
            print("[recognize_from_bytes] incoming bytes:", len(wav_bytes), "samplerate:", samplerate)

        # Create AudioData object for SR
        audio_data = sr.AudioData(wav_bytes, int(samplerate), int(sample_width))

        r = sr.Recognizer()

        try:
            text = r.recognize_google(audio_data)
            if show_debug:
                print("[recognize_from_bytes] Recognized text:", text)
            return True, text
        except sr.UnknownValueError:
            return False, "Sorry, could not understand the audio."
        except sr.RequestError as e:
            return False, f"STT request error: {e}"

    except Exception as e:
        print("[recognize_from_bytes] Exception:", e)
        return False, f"Recognition error: {e}"

def record_sound(duration=RECORD_DURATION, samplerate=SAMPLERATE, channels=CHANNELS):
    """
    Record audio using sounddevice and return WAV bytes (PCM16).
    Returns: (True, wav_bytes) on success or (False, error_message).
    """
    if sd is None or sf is None:
        return False, "sounddevice or soundfile not installed"

    try:
        samplerate = int(samplerate)
        try:
            devs = sd.query_devices()
            print("[record_sound] default device:", sd.default.device, "device count:", len(devs))
        except Exception as e:
            print("[record_sound] device query failed:", e)

        frames = int(duration * samplerate)
        print(f"[record_sound] Recording {duration}s -> {frames} frames @ {samplerate}Hz")
        rec = sd.rec(frames, samplerate=samplerate, channels=channels, dtype='int16')
        sd.wait()
        print("[record_sound] Recording finished, shape:", getattr(rec, "shape", None))

        buf = io.BytesIO()
        sf.write(buf, rec, samplerate, format='WAV', subtype='PCM_16')
        buf.seek(0)
        wav_bytes = buf.read()
        print("[record_sound] WAV bytes length:", len(wav_bytes))
        return True, wav_bytes

    except Exception as e:
        print("[record_sound] Exception:", e)
        return False, f"Recording failed: {e}"

def safe_eval_expr(expr: str):
    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
        ast.USub, ast.UAdd, ast.Load, ast.Tuple, ast.List, ast.Subscript,
        ast.LShift, ast.RShift, ast.BitXor, ast.BitAnd, ast.BitOr
    )

    # Parse
    try:
        parsed = ast.parse(expr, mode="eval")
    except Exception as e:
        raise ValueError("Invalid expression")

    # Walk nodes and ensure they're allowed
    for node in ast.walk(parsed):
        if not isinstance(node, allowed_nodes):
            raise ValueError("Unsupported expression element: " + node.__class__.__name__)

    # Evaluate safely via compile
    try:
        code = compile(parsed, "<string>", "eval")
        # limit builtins
        return eval(code, {"__builtins__": {}}, {})
    except Exception as e:
        raise ValueError("Could not evaluate expression")

# Weather helpers using Open-Meteo
def get_location_by_ip():
    try:
        r = requests.get("https://ipinfo.io/json", timeout=5)
        r.raise_for_status()
        j = r.json()
        loc = j.get("loc")
        city = j.get("city")
        if loc:
            lat, lon = loc.split(",")
            return float(lat), float(lon), city
    except Exception:
        pass
    return None, None, None

def get_weather_open_meteo(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        j = r.json()
        cw = j.get("current_weather", {})
        temp = cw.get("temperature")
        wind = cw.get("windspeed")
        weathercode = cw.get("weathercode")
        code_map = {
            0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
            45: "fog", 48: "depositing rime fog", 51: "light drizzle", 61: "rain",
            71: "snow", 80: "rain showers", 95: "thunderstorm"
        }
        desc = code_map.get(weathercode, "current conditions")
        return True, f"{desc}. Temperature {temp}°C. Wind speed {wind} km/h."
    except Exception as e:
        return False, f"Weather fetch failed: {e}"

# Knowledge via Wikipedia
def wiki_summary(query):
    try:
        wikipedia.set_lang("en")
        s = wikipedia.summary(query, sentences=2)
        return True, s
    except Exception as e:
        return False, f"Wikipedia error: {e}"

# News via Feedparser
def get_news():
    try:
        # BBC News RSS Feed
        feed = feedparser.parse("http://feeds.bbci.co.uk/news/rss.xml")
        headlines = [entry.title for entry in feed.entries[:3]]
        if headlines:
            return "Here are the top news headlines: " + ". ".join(headlines)
        else:
            return "Sorry, I couldn't fetch the news right now."
    except Exception as e:
        return f"Error fetching news: {e}"

# Jokes via Pyjokes
def get_joke():
    try:
        return pyjokes.get_joke()
    except Exception:
        return "Why did the chicken cross the road? To get to the other side."

# Simple intent handler
def get_bot_reply(user_text: str):
    if not user_text:
        return "Sorry, I didn't catch that."
    text = user_text.lower().strip()
    # weather intent
    if "weather" in text:
        m = re.search(r"weather (?:in|at)\s+([a-zA-Z \-]+)", text)
        city = None
        if m:
            city = m.group(1).strip()
        if city:
            try:
                geocode = requests.get("https://nominatim.openstreetmap.org/search", params={"q": city, "format":"json", "limit":1}, headers={"User-Agent":"audio-chatbot"} , timeout=8)
                geocode.raise_for_status()
                gj = geocode.json()
                if gj:
                    lat = float(gj[0]["lat"]); lon = float(gj[0]["lon"])
                    ok, resp = get_weather_open_meteo(lat, lon)
                    if ok:
                        return f"Weather in {city}: {resp}"
            except Exception:
                pass
            return f"Sorry, couldn't fetch weather for {city}."
        lat, lon, city = get_location_by_ip()
        if lat is None:
            return "Please tell me the city for which you want the weather, for example: 'weather in Mumbai'."
        ok, resp = get_weather_open_meteo(lat, lon)
        if ok:
            place = city if city else "your location"
            return f"Weather for {place}: {resp}"
        else:
            return resp

    # time/date
    if "time" in text:
        return f"The time is {time.strftime('%I:%M %p')}."
    if "date" in text or "day" in text:
        return f"Today is {time.strftime('%A, %B %d, %Y')}."

 # math 
    m = re.search(r"(?:what is|what's|calculate|evaluate)\s+(.+)", text)
    if m:
        expr = m.group(1).strip()
        # remove trailing question mark or words
        expr = re.sub(r"[?]", "", expr)
        # common word-to-operator replacements (optional)
        expr = expr.replace("x", "*").replace("X", "*").replace("×", "*")
        expr = expr.replace("times", "*").replace("divided by", "/")
        try:
            result = safe_eval_expr(expr)
            # format integers without .0
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return f"The answer is {result}."
        except ValueError:
            # fallback: try to match simple two-number operator forms (already handled earlier)
            pass
        
    # wiki/what is intent
    if text.startswith("who is") or text.startswith("what is") or text.startswith("tell me about"):
        q = re.sub(r"^(who is|what is|tell me about)\s+", "", text)
        ok, resp = wiki_summary(q)
        if ok:
            return resp
        else:
            return resp

    # greetings
    if any(g in text for g in ("hello", "hi", "hey")):
        return "Hello! How can I help you today?"

    # jokes
    if "joke" in text or "funny" in text:
        return get_joke()

    # news
    if "news" in text or "headlines" in text:
        return get_news()

    return "I heard: " + user_text + ". You can ask about weather, news, jokes, or general knowledge."

if listen_btn:
    status.info("Recording...")
    # Record (blocking)
    ok, wav = record_sound(duration=record_dur)
    if not ok:
        status.error(wav)
    else:
        status.info("Recognizing...")
        ok2, text = recognize_from_bytes(wav, samplerate=SAMPLERATE)
        if not ok2:
            status.error(text)
        else:
            st.session_state['history'].append(("You", text))
            status.success("Recognized: " + text)
            reply = get_bot_reply(text)
            st.session_state['history'].append(("Bot", reply))
            audio_bytes = tts_bytes(reply)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3", autoplay=True)
            else:
                st.warning("TTS failed or no internet for gTTS/ElevenLabs.")

# Typed String
if send_btn and typed.strip():
    user_text = typed.strip()
    st.session_state['history'].append(("You", user_text))
    reply = get_bot_reply(user_text)
    st.session_state['history'].append(("Bot", reply))
    audio_bytes = tts_bytes(reply)
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

# Render conversation history using st.chat_message
if st.session_state['history']:
    st.markdown("### Conversation")
    for who, text in st.session_state['history']:
        if who == "You":
            with st.chat_message("user"):
                st.write(text)
        else:
            with st.chat_message("assistant"):
                st.write(text)
else:
    st.write("No conversation yet. Say something or type a message.")

st.caption("Note: Recording uses sounddevice. Open-Meteo and Wikipedia are free APIs.")