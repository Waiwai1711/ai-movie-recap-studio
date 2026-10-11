import os
from typing import List

class SubtitleService:
    @classmethod
    def generate_srt(cls, sentences: List[str], sentence_durations: List[float], output_srt_path: str) -> str:
        os.makedirs(os.path.dirname(output_srt_path), exist_ok=True)
        
        def format_time(seconds: float) -> str:
            millis = int((seconds - int(seconds)) * 1000)
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

        srt_content = []
        current_time = 0.0

        for i, (text, dur) in enumerate(zip(sentences, sentence_durations), 1):
            start_str = format_time(current_time)
            end_time = current_time + dur
            end_str = format_time(end_time)
            
            srt_content.append(f"{i}\n{start_str} --> {end_str}\n{text.strip()}\n")
            current_time = end_time

        full_srt = "\n".join(srt_content)
        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write(full_srt)
            
        return full_srt
