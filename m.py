from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import sys
import time
from gtts import gTTS
import pygame
import os
import speech_recognition as sr
import google.generativeai as genai  # NEW

# ---------------- Flask Init ----------------
app = Flask(__name__)
CORS(app)

# ---------------- Gemini Setup ----------------
# Try to load API key from environment variable first
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Fallback: hardcoded key (⚠ only for testing; remove before sharing)
if not GEMINI_API_KEY:
    GEMINI_API_KEY = "AIzaSyAMMhfGr0KDeeLdT1NiCz1vn8VyIzGYu0M"   # <-- paste your Gemini API key here

genai.configure(api_key=GEMINI_API_KEY)

# Use lightweight free model
gemini_model = genai.GenerativeModel("gemini-1.5-flash")


# ---------------- Helper Functions ----------------
def speak(text):
    """Convert text to speech using pyttsx3 (subprocess) or gTTS fallback."""
    safe_text = str(text)

    # Try pyttsx3 first
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

    # Fallback: gTTS + pygame
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
    """Generate chatbot response using Gemini API instead of Naive Bayes."""
    try:
        response = gemini_model.generate_content(user_input)
        return response.text.strip()
    except Exception as e:
        return f"❌ Gemini API error: {e}"


def speech_to_text():
    """Convert speech (from microphone) to text."""
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
    """Chat via text (now powered by Gemini API)"""
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
    """Convert speech (via mic) to text"""
    result = speech_to_text()
    return jsonify({"text": result})


@app.route("/chat_via_speech", methods=["GET"])
def api_chat_via_speech():
    """Listen speech -> convert to text -> chatbot response -> speak back"""
    user_text = speech_to_text()
    if user_text.startswith("❌"):
        return jsonify({"error": user_text})

    bot_response = chatbot_response(user_text)
    speak(bot_response)  # speak out response

    return jsonify({
        "user_text": user_text,
        "bot_response": bot_response
    })


if __name__ == "__main__":
    app.run(port=5000, debug=True)






# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import pandas as pd
# from sklearn.feature_extraction.text import CountVectorizer
# from sklearn.naive_bayes import MultinomialNB
# import subprocess
# import sys
# import time
# from gtts import gTTS
# import pygame
# import os
# import speech_recognition as sr

# app = Flask(__name__)
# CORS(app)  # allow frontend (React) to connect

# # --- Load Chat Dataset & Train Chatbot Model ---
# chat_model = None
# chat_vectorizer = None
# try:
#     df = pd.read_csv("train_enhanced.csv")  # chatbot training CSV
#     inputs = df["User_Input"].astype(str).tolist()
#     responses = df["Chatbot_Response"].astype(str).tolist()

#     chat_vectorizer = CountVectorizer()
#     X = chat_vectorizer.fit_transform(inputs)
#     chat_model = MultinomialNB()
#     chat_model.fit(X, responses)

#     print("✅ Chatbot Model Trained Successfully!")
# except FileNotFoundError:
#     print("❌ Error: 'train_enhanced.csv' not found.")
# except Exception as e:
#     print(f"❌ Error loading/training chatbot dataset: {e}")


# # --- Helper Functions ---
# def speak(text):
#     """Convert text to speech using pyttsx3 (subprocess) or gTTS fallback."""
#     safe_text = str(text)

#     # Try pyttsx3 first
#     try:
#         subprocess.run([sys.executable, "-c", f"""
# import pyttsx3
# engine = pyttsx3.init()
# engine.setProperty("rate", 170)
# engine.setProperty("volume", 1.0)
# voices = engine.getProperty("voices")
# if voices: engine.setProperty("voice", voices[0].id)
# engine.say({repr(safe_text)})
# engine.runAndWait()
# """], check=True)
#         return "Spoken successfully"
#     except Exception as e:
#         print(f"⚠ pyttsx3 failed ({e}), using gTTS fallback...")

#     # Fallback: gTTS + pygame
#     try:
#         tts = gTTS(text=safe_text, lang="en")
#         filename = "temp_tts.mp3"
#         tts.save(filename)

#         pygame.mixer.init()
#         pygame.mixer.music.load(filename)
#         pygame.mixer.music.play()

#         while pygame.mixer.music.get_busy():
#             time.sleep(0.1)

#         pygame.mixer.music.unload()
#         pygame.mixer.quit()
#         os.remove(filename)
#         return "Spoken successfully (gTTS)"
#     except Exception as e2:
#         return f"❌ Both pyttsx3 and gTTS failed: {e2}"


# def chatbot_response(user_input):
#     """Generate chatbot response using trained model."""
#     if chat_model is None or chat_vectorizer is None:
#         return "Sorry, I am not trained yet."
#     input_vec = chat_vectorizer.transform([user_input])
#     return chat_model.predict(input_vec)[0]


# def speech_to_text():
#     """Convert speech (from microphone) to text."""
#     recognizer = sr.Recognizer()
#     with sr.Microphone() as source:
#         print("🎤 Listening...")
#         audio = recognizer.listen(source)
#     try:
#         return recognizer.recognize_google(audio)
#     except sr.UnknownValueError:
#         return "❌ Could not understand audio"
#     except sr.RequestError as e:
#         return f"❌ Speech recognition error: {e}"


# # --- Flask Routes ---
# @app.route("/", methods=["GET"])
# def home():
#     return jsonify({"status": "Chatbot backend running ✅"})


# @app.route("/chat", methods=["POST"])
# def chat():
#     """Chat via text"""
#     data = request.get_json()
#     user_message = data.get("message", "")
#     if not user_message.strip():
#         return jsonify({"response": "Please type something."})
#     response = chatbot_response(user_message)
#     return jsonify({"response": response})


# @app.route("/speak", methods=["POST"])
# def api_speak():
#     """Convert text to speech"""
#     data = request.get_json()
#     text = data.get("text", "")
#     if not text.strip():
#         return jsonify({"status": "No text to speak"})
#     result = speak(text)
#     return jsonify({"status": result})


# @app.route("/speech_to_text", methods=["GET"])
# def api_speech_to_text():
#     """Convert speech (via mic) to text"""
#     result = speech_to_text()
#     return jsonify({"text": result})


# @app.route("/chat_via_speech", methods=["GET"])
# def api_chat_via_speech():
#     """Listen speech -> convert to text -> chatbot response -> speak back"""
#     user_text = speech_to_text()
#     if user_text.startswith("❌"):
#         return jsonify({"error": user_text})

#     bot_response = chatbot_response(user_text)
#     speak(bot_response)  # speak out response

#     return jsonify({
#         "user_text": user_text,
#         "bot_response": bot_response
#     })


# if __name__ == "__main__":
#     app.run(port=5000, debug=True)
