from openai import OpenAI
import base64
from pathlib import Path


def process_audio(data):
    BASE_DIR = Path(__file__).resolve().parent.parent
    path = BASE_DIR/'audio.ogg'
    
    base64_audio = data.get("base64")
    with open("audio.ogg", "wb") as f:
        f.write(base64.b64decode(base64_audio))

    client = OpenAI()
    audio_file= open(path, "rb")

    transcription = client.audio.transcriptions.create(
        model="gpt-4o-transcribe", 
        file=audio_file
    )

    return transcription.text