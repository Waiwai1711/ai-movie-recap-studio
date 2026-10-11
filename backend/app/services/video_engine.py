import os
import json
import subprocess
from typing import Dict, Any, List, Optional

def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {proc.stderr[-500:]}")
    return proc

def probe_media(file_path: str) -> Dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise ValueError(f"Invalid media file or ffprobe missing: {proc.stderr}")
    data = json.loads(proc.stdout)
    
    duration = float(data.get("format", {}).get("duration", 0.0))
    video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    
    width = int(video_stream.get("width", 0)) if video_stream else 0
    height = int(video_stream.get("height", 0)) if video_stream else 0
    
    return {
        "duration": duration,
        "width": width,
        "height": height,
        "has_audio": audio_stream is not None,
        "format": data.get("format", {}).get("format_name", "")
    }

def extract_audio(video_path: str, output_wav_path: str) -> str:
    os.makedirs(os.path.dirname(output_wav_path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_wav_path
    ]
    run_cmd(cmd)
    return output_wav_path

def detect_scenes_and_thumbnails(video_path: str, output_dir: str, threshold: float = 0.3) -> List[Dict[str, Any]]:
    os.makedirs(output_dir, exist_ok=True)
    scenes = []
    meta = probe_media(video_path)
    total_dur = meta["duration"]
    
    interval = max(5.0, total_dur / 10.0) if total_dur > 0 else 5.0
    cur = 0.0
    idx = 0
    while cur < total_dur:
        end = min(total_dur, cur + interval)
        thumb_file = os.path.join(output_dir, f"scene_{idx:03d}.jpg")
        mid = cur + (end - cur) / 2.0
        thumb_cmd = [
            "ffmpeg", "-y",
            "-ss", str(mid),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "3",
            thumb_file
        ]
        try:
            run_cmd(thumb_cmd)
        except Exception:
            pass
            
        scenes.append({
            "index": idx,
            "start": round(cur, 2),
            "end": round(end, 2),
            "thumbnail": thumb_file
        })
        cur = end
        idx += 1
        
    return scenes

def render_movie_recap(
    source_video: str,
    narration_audio: str,
    output_mp4: str,
    subtitles_srt: Optional[str] = None,
    aspect_ratio: str = "16:9",
    target_duration: float = 180.0
) -> str:
    os.makedirs(os.path.dirname(output_mp4), exist_ok=True)
    
    probe_a = probe_media(narration_audio)
    actual_audio_dur = probe_a["duration"]
    
    if aspect_ratio == "9:16":
        scale_filter = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"
    else:
        scale_filter = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"

    vf_chain = scale_filter
    if subtitles_srt and os.path.exists(subtitles_srt):
        escaped_srt = subtitles_srt.replace("\\", "/").replace(":", "\\:")
        style = "FontSize=20,FontName=Pyidaungsu,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Alignment=2,MarginV=30"
        vf_chain += f",subtitles='{escaped_srt}':force_style='{style}'"

    cmd = [
        "ffmpeg", "-y",
        "-ss", "0",
        "-t", str(actual_audio_dur),
        "-i", source_video,
        "-i", narration_audio,
        "-vf", vf_chain,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "faster",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        output_mp4
    ]
    run_cmd(cmd)
    
    out_meta = probe_media(output_mp4)
    if out_meta["duration"] < 0.5:
        raise RuntimeError("Rendered file duration is corrupted.")
        
    return output_mp4
