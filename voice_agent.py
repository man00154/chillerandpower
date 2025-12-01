import io
from google.cloud import speech_v1p1beta1 as speech
import pyttsx3


def transcribe_google(raw_bytes):
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(content=raw_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code="en-US"
    )

    response = client.recognize(config=config, audio=audio)

    text = ""
    for result in response.results:
        text += result.alternatives[0].transcript

    return text


def tts_play(text):
    engine = pyttsx3.init()
    engine.save_to_file(text, "reply.wav")
    engine.runAndWait()

    with open("reply.wav", "rb") as f:
        return f.read()
