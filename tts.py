import os
import requests
from typing import Optional

try:

    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def generate_tts(title: str, text: str, gender: str) -> Optional[tuple]:
    voice = "bella" if gender == "female" else "adam"
    url = "https://api.lemonfox.ai/v1/audio/speech"

    api_key = os.getenv("TTS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "TTS_API_KEY not found in environment. Add it to .env as TTS_API_KEY=your_key"
        )

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }

    def get_audio(input_text, filename):
        data = {
            "input": input_text,
            "voice": voice,
            "response_format": "wav"
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            try:
                with open(filename, "wb") as f:
                    f.write(response.content)

                print(f"TTS generated successfully: {filename}")
                return filename
            except Exception as e:
                print(f"Error writing audio file: {e}")
                return None
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return None

    title_filename = "title_audio.wav"
    text_filename = "story_audio.wav"

    title_file = get_audio(title, title_filename)
    text_file = get_audio(text, text_filename)

    return title_file, text_file
