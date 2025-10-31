from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import sys
import time
from gtts import gTTS
import pygame
import os
import speech_recognition as sr
import google.generativeai as genai

# ---------------- Flask Init ----------------
app = Flask(__name__)
CORS(app)

# ---------------- Gemini Setup ----------------
# Load API key from environment variable, fallback to manual key
GEMINI_API_KEY ="AIzaSyDnjexmDSRGQf4-s8iUcBedgPK6a63egc0"  # ⚠ Replace for production

genai.configure(api_key=GEMINI_API_KEY)

# Use valid Gemini model name
try:
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    print(f"⚠ Model init failed: {e}")
    gemini_model = None


# ---------------- Helper Functions ----------------
def speak(text):
    """Convert text to speech using pyttsx3 or gTTS fallback."""
    safe_text = str(text)
    try:
        subprocess.run([sys.executable, "-c", f"""
import pyttsx3
engine = pyttsx3.init()
engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)
voices = engine.getProperty("voices")
if voices: engine.setProperty("voice", voices[0].id)
engine.say({repr(safe_text)})
engine.runAndWait()
"""], check=True)
        return "Spoken successfully"
    except Exception as e:
        print(f"⚠ pyttsx3 failed ({e}), using gTTS fallback...")

    try:
        tts = gTTS(text=safe_text, lang="en")
        filename = "temp_tts.mp3"
        tts.save(filename)

        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        pygame.mixer.music.unload()
        pygame.mixer.quit()
        os.remove(filename)
        return "Spoken successfully (gTTS)"
    except Exception as e2:
        return f"❌ Both pyttsx3 and gTTS failed: {e2}"


def chatbot_response(user_input):
    """Generate chatbot response using Gemini API."""
    if not gemini_model:
        return "❌ Gemini model not initialized."

    try:
        # Gemini generate_content expects dict-like input
        response = gemini_model.generate_content(
            contents=[{"role": "user", "parts": [{"text": user_input}]}]
        )
        # Handle Gemini API result properly
        if hasattr(response, "text") and response.text:
            return response.text.strip()
        elif hasattr(response, "candidates") and response.candidates:
            return response.candidates[0].content.parts[0].text
        else:
            return "⚠ No valid response from Gemini API."
    except Exception as e:
        return f"❌ Gemini API error: {e}"


def speech_to_text():
    """Convert speech from mic to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "❌ Could not understand audio"
    except sr.RequestError as e:
        return f"❌ Speech recognition error: {e}"


# ---------------- Flask Routes ----------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Chatbot backend running ✅"})


@app.route("/chat", methods=["POST"])
def chat():
    """Chat via text (Gemini-based)"""
    data = request.get_json()
    user_message = data.get("message", "")
    if not user_message.strip():
        return jsonify({"response": "Please type something."})
    response = chatbot_response(user_message)
    return jsonify({"response": response})


@app.route("/speak", methods=["POST"])
def api_speak():
    """Convert text to speech"""
    data = request.get_json()
    text = data.get("text", "")
    if not text.strip():
        return jsonify({"status": "No text to speak"})
    result = speak(text)
    return jsonify({"status": result})


@app.route("/speech_to_text", methods=["GET"])
def api_speech_to_text():
    """Convert speech to text"""
    result = speech_to_text()
    return jsonify({"text": result})


@app.route("/chat_via_speech", methods=["GET"])
def api_chat_via_speech():
    """Speech → Text → Gemini → Speak → Response"""
    user_text = speech_to_text()
    if user_text.startswith("❌"):
        return jsonify({"error": user_text})

    bot_response = chatbot_response(user_text)
    speak(bot_response)
    return jsonify({
        "user_text": user_text,
        "bot_response": bot_response
    })


if __name__ == "__main__":
    app.run(port=5000, debug=True)
