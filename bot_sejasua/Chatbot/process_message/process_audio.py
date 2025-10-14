from openai import OpenAI
import base64


def process_audio(data):
    base64_audio = data.get("base64")
    with open("audio.ogg", "wb") as f:
        f.write(base64.b64decode(base64_audio))

    client = OpenAI()
    audio_file= open("/root/chatbots/bot_sejasua/Chatbot/audio.ogg", "rb")

    transcription = client.audio.transcriptions.create(
        model="gpt-4o-transcribe", 
        file=audio_file
    )

    return transcription.text