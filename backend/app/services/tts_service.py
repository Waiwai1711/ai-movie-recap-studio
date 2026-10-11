import os
import edge_tts
from typing import Dict, List

SUPPORTED_VOICES = {
    "my": [
        {"id": "my-MM-ThihaNeural", "name": "Thiha (Burmese Male - Natural)"},
        {"id": "my-MM-NilarNeural", "name": "Nilar (Burmese Female - Natural)"}
    ],
    "en": [
        {"id": "en-US-ChristopherNeural", "name": "Christopher (English Male - Dramatic)"},
        {"id": "en-US-JennyNeural", "name": "Jenny (English Female - Storyteller)"},
        {"id": "en-US-GuyNeural", "name": "Guy (English Male - Action Recap)"}
    ]
}

class TTSService:
    @classmethod
    def get_voices_for_language(cls, lang: str) -> List[Dict[str, str]]:
        return SUPPORTED_VOICES.get(lang, SUPPORTED_VOICES["en"])

    @classmethod
    async def synthesize(cls, text: str, voice: str, output_audio_path: str) -> str:
        os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
        if not text.strip():
            raise ValueError("Narration text is empty.")

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_audio_path)
        
        if not os.path.exists(output_audio_path) or os.path.getsize(output_audio_path) == 0:
            raise RuntimeError("TTS generation produced an empty audio file.")
            
        return output_audio_path
