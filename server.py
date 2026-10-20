import json  
import os  
import re  
import socket  
import sys  
import tempfile  
import threading  
import time  
import wave  
import numpy as np  
import pythoncom  
import pyttsx3  
import sounddevice as sd  
import speech_recognition as sr  
from flask import Flask, request, jsonify  
from google import genai  
from google.genai import types  
  
# Configuración de codificación UTF-8 para consola en Windows  
if sys.platform == "win32":  
    try:  
        sys.stdout.reconfigure(encoding="utf-8")  
        sys.stderr.reconfigure(encoding="utf-8")  
    except Exception:  
        pass  
  
# Cargar variables de entorno desde archivo .env si existe  
env_file = os.path.join(os.path.dirname(__file__), ".env")  
if os.path.exists(env_file):  
    with open(env_file, "r", encoding="utf-8") as f:  
        for line in f:  
            line = line.strip()  
            if line and not line.startswith("#") and "=" in line:  
                key, val = line.split("=", 1)  
                os.environ.setdefault(key.strip(), val.strip())  
  
API_KEY = os.environ.get("GEMINI_API_KEY", "TU_API_KEY_AQUI")  
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")  
HOST = os.environ.get("HOST", "0.0.0.0")  
PORT = int(os.environ.get("PORT", "8000"))  
  
# Inicializar cliente de Google GenAI  
client = genai.Client(api_key=API_KEY)  
  
# Configuración de respuestas breves de Gemini
gemini_config = types.GenerateContentConfig(  
    system_instruction="Responde SIEMPRE en máximo 1 o 2 oraciones breves y conversacionales (menos de 25 palabras). No uses listas, viñetas, Markdown ni asteriscos. Habla directo y al grano en español.",  
    max_output_tokens=80,  
    temperature=0.7,  
)  
  
app = Flask(__name__)  
app.config['JSON_AS_ASCII'] = False  
try:  
    app.json.ensure_ascii = False  
except Exception:  
    pass  
  
is_speaking = False  
tts_lock = threading.Lock()  
  
def stop_audio():  
    global is_speaking  
    is_speaking = False  
    try:  
        sd.stop()  
    except Exception as e:  
        print(f"[AUDIO] Error en sd.stop(): {e}", file=sys.stderr)  
  
def clean_markdown_for_speech(text: str) -> str:  
    if not text: return ""  
    cleaned = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  
    cleaned = re.sub(r'[\*\#\_\`\~]', '', cleaned)  
    cleaned = re.sub(r'\n+', '. ', cleaned)  
    return cleaned.strip()  
  
def speak_text(text: str):  
    global is_speaking  
    speech_text = clean_markdown_for_speech(text)  
    if not speech_text: return  
  
    stop_audio()  
    temp_wav = os.path.join(tempfile.gettempdir(), f"gemini_tts_{os.getpid()}_{int(time.time() * 1000)}.wav")  
  
    with tts_lock:  
        try:  
            pythoncom.CoInitialize()  
            engine = pyttsx3.init()  
            engine.setProperty("rate", 175)  
            voices = engine.getProperty("voices")  
            for v in voices:  
                if any(lang in v.name.lower() or lang in v.id.lower() for lang in ["spanish", "es-es", "es-mx"]):  
                    engine.setProperty("voice", v.id)  
                    break  
            engine.save_to_file(speech_text, temp_wav)  
            engine.runAndWait()  
            engine.stop()  
        except Exception as e:  
            print(f"[TTS] Error: {e}", file=sys.stderr)  
            return  
        finally:  
            try: pythoncom.CoUninitialize()  
            except: pass  
  
    if not os.path.exists(temp_wav): return  
  
    try:  
        with wave.open(temp_wav, "rb") as wf:  
            framerate = wf.getframerate()  
            frames = wf.readframes(wf.getnframes())  
            audio_data = np.frombuffer(frames, dtype=np.int16)  
        is_speaking = True  
        sd.play(audio_data, samplerate=framerate)  
        sd.wait()  
    except Exception as e:  
        print(f"[TTS] Error de audio: {e}", file=sys.stderr)  
    finally:  
        is_speaking = False  
        try: os.remove(temp_wav)  
        except: pass  
  
def speak_text_async(text: str):  
    threading.Thread(target=speak_text, args=(text,), daemon=True).start()  

@app.route("/chat", methods=["POST"])  
def chat():  
    data = request.get_json(force=True, silent=True) or {}  
    prompt = data.get("prompt")  
    if not prompt or not str(prompt).strip():  
        return jsonify({"error": "El campo 'prompt' es requerido."}), 400  
  
    try:
        response = client.models.generate_content(
