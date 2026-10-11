import httpx
from typing import Optional
from app.config import settings

class LLMScriptService:
    @classmethod
    async def generate_recap_script(
        cls,
        transcript: str,
        target_language: str = "my",
        target_duration_minutes: int = 3,
        user_api_key: Optional[str] = None
    ) -> str:
        api_key = user_api_key or settings.OPENAI_API_KEY or settings.OPENROUTER_API_KEY
        
        system_prompt = (
            "You are an expert cinematic movie recap narrator and scriptwriter. "
            f"Condense the provided movie transcript into an engaging recap script for a {target_duration_minutes}-minute video.\n"
        )
        
        if target_language == "my":
            system_prompt += (
                "CRITICAL REQUIREMENT: Write narration entirely in dramatic Burmese Unicode (မြန်မာဘာသာ). "
                "Do not include stage directions like [Scene 1]."
            )
        else:
            system_prompt += "Write fluent, high-energy English narration ready for voiceover."

        if not api_key:
            sentences = [s.strip() for s in transcript.split(".") if len(s.strip()) > 15]
            picked = sentences[:min(12, len(sentences))]
            if target_language == "my":
                return "ဒီဇာတ်ကားမှာတော့ စိတ်လှုပ်ရှားဖွယ် ဇာတ်လမ်းစတင်လာပါတယ်။ " + "။ ".join(picked[:6]) + "။ နောက်ဆုံးမှာတော့ မထင်မှတ်ထားတဲ့ အဆုံးသတ်နဲ့ ပြီးဆုံးသွားခဲ့ပါတယ်။"
            return "In this thrilling story, our main protagonist faces unexpected events. " + ". ".join(picked) + "."

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Movie Transcript:\n{transcript[:15000]}"}
                    ],
                    "temperature": 0.7
                }
            )
            if resp.status_code != 200:
                raise RuntimeError(f"LLM API Error ({resp.status_code}): {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
