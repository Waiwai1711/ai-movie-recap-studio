import httpx
import asyncio
from typing import Dict, Any

class AssemblyAIService:
    BASE_URL = "https://api.assemblyai.com/v2"

    @classmethod
    async def upload_audio_file(cls, api_key: str, file_path: str) -> str:
        headers = {"Authorization": api_key}
        async with httpx.AsyncClient(timeout=300.0) as client:
            with open(file_path, "rb") as f:
                response = await client.post(
                    f"{cls.BASE_URL}/upload",
                    headers=headers,
                    content=f.read()
                )
            if response.status_code != 200:
                raise RuntimeError(f"AssemblyAI Upload failed: {response.text}")
            return response.json()["upload_url"]

    @classmethod
    async def transcribe(cls, api_key: str, audio_file_path: str, poll_interval: int = 4) -> Dict[str, Any]:
        upload_url = await cls.upload_audio_file(api_key, audio_file_path)
        headers = {"Authorization": api_key, "Content-Type": "application/json"}
        
        payload = {
            "audio_url": upload_url,
            "speaker_labels": True,
            "punctuate": True,
            "format_text": True
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            start_resp = await client.post(
                f"{cls.BASE_URL}/transcript",
                headers=headers,
                json=payload
            )
            if start_resp.status_code != 200:
                raise RuntimeError(f"AssemblyAI Transcription trigger failed: {start_resp.text}")
            transcript_id = start_resp.json()["id"]

        while True:
            await asyncio.sleep(poll_interval)
            async with httpx.AsyncClient(timeout=30.0) as client:
                poll_resp = await client.get(
                    f"{cls.BASE_URL}/transcript/{transcript_id}",
                    headers=headers
                )
                data = poll_resp.json()
                status = data.get("status")
                
                if status == "completed":
                    return {
                        "text": data.get("text", ""),
                        "words": data.get("words", []),
                        "confidence": data.get("confidence", 0.0)
                    }
                elif status == "error":
                    raise RuntimeError(f"AssemblyAI error: {data.get('error')}")
