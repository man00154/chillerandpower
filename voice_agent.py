import io
import speech_recognition as sr
from gtts import gTTS


def transcribe_voice(raw_bytes: bytes) -> str:
    """
    Use SpeechRecognition + free Google Web Speech API to transcribe audio.
    No API key required, but requires internet and fair-use limits.

    Expecting raw WAV bytes from Streamlit file uploader.
    """
    if not raw_bytes:
        return ""

    recognizer = sr.Recognizer()

    # Wrap raw bytes as a file-like object for AudioFile
    audio_file = sr.AudioFile(io.BytesIO(raw_bytes))

    with audio_file as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio)
        return text.strip()
    except sr.UnknownValueError:
        # Speech unintelligible
        return ""
    except sr.RequestError as e:
        # API unreachable or rate-limited
        return f"[STT request error: {e}]"


def tts_voice(text: str) -> bytes:
    """
    Use gTTS (Google Translate Text-to-Speech) to synthesize speech.
    No API key is needed. Returns MP3 audio bytes.
    """
    if not text:
        text = "I do not have anything to say."

    tts = gTTS(text=text, lang="en")
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()
