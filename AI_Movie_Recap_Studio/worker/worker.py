import os
import sys
import time
import asyncio
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.config import settings
from app.models import Job, Project, User
from app.security import decrypt_api_key
from app.services.video_engine import probe_media, render_movie_recap
from app.services.assemblyai_service import AssemblyAIService
from app.services.llm_service import LLMScriptService
from app.services.tts_service import TTSService
from app.services.subtitle_service import SubtitleService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("worker")

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

async def process_job(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job or job.status != "QUEUED":
            return

        job.status = "RUNNING"
        job.stage = "starting"
        job.progress = 5
        db.commit()

        proj = db.query(Project).filter(Project.id == job.project_id).first()
        user = db.query(User).filter(User.id == job.user_id).first()
        if not proj or not user:
            job.status = "FAILED"
            job.error_message = "Project or user missing."
            db.commit()
            return

        p_dir = os.path.dirname(proj.source_video_path)

        if not proj.transcript_text:
            job.stage = "transcribing_audio"
            job.progress = 15
            db.commit()

            aai_key = decrypt_api_key(user.encrypted_assemblyai_key) if user.encrypted_assemblyai_key else settings.ASSEMBLYAI_ADMIN_KEY
            if not aai_key:
                raise ValueError("No AssemblyAI API Key found. Add key in Settings.")

            transcription = await AssemblyAIService.transcribe(aai_key, proj.source_audio_path)
            proj.transcript_text = transcription["text"]
            db.commit()

        db.refresh(job)
        if job.status == "CANCELLED":
            return

        if not proj.script_text:
            job.stage = "generating_script"
            job.progress = 35
            db.commit()

            llm_key = decrypt_api_key(user.encrypted_llm_key) if user.encrypted_llm_key else None
            script = await LLMScriptService.generate_recap_script(
                transcript=proj.transcript_text,
                target_language=proj.target_language,
                target_duration_minutes=proj.target_duration_minutes,
                user_api_key=llm_key
            )
            proj.script_text = script
            db.commit()

        db.refresh(job)
        if job.status == "CANCELLED":
            return

        job.stage = "synthesizing_tts"
        job.progress = 55
        db.commit()

        narration_wav = os.path.join(p_dir, "narration.mp3")
        await TTSService.synthesize(proj.script_text, proj.voice_name, narration_wav)

        job.stage = "generating_subtitles"
        job.progress = 70
        db.commit()

        tts_probe = probe_media(narration_wav)
        total_audio_sec = tts_probe["duration"]

        raw_sentences = [s.strip() for s in proj.script_text.replace("။", "။\n").split("\n") if s.strip()]
        if not raw_sentences:
            raw_sentences = [proj.script_text]

        total_chars = sum(len(s) for s in raw_sentences)
        durations = [(len(s) / max(1, total_chars)) * total_audio_sec for s in raw_sentences]
        
        srt_file = os.path.join(p_dir, "subtitles.srt")
        srt_data = SubtitleService.generate_srt(raw_sentences, durations, srt_file)
        proj.subtitles_srt = srt_data
        db.commit()

        job.stage = "rendering_ffmpeg"
        job.progress = 85
        db.commit()

        output_mp4 = os.path.join(p_dir, f"{proj.title.replace(' ', '_')}_final.mp4")
        render_movie_recap(
            source_video=proj.source_video_path,
            narration_audio=narration_wav,
            output_mp4=output_mp4,
            subtitles_srt=srt_file if proj.burn_subtitles else None,
            aspect_ratio=proj.aspect_ratio,
            target_duration=total_audio_sec
        )

        proj.rendered_video_path = output_mp4
        proj.status = "completed"
        
        job.stage = "completed"
        job.progress = 100
        job.status = "COMPLETED"
        db.commit()

    except Exception as e:
        logger.error(f"Render job failed: {str(e)}")
        db.rollback()
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "FAILED"
            job.stage = "failed"
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()

def main_loop():
    logger.info("Worker started.")
    while True:
        db = SessionLocal()
        try:
            running_count = db.query(Job).filter(Job.status == "RUNNING").count()
            if running_count < settings.MAX_CONCURRENT_RENDERS_GLOBAL:
                next_job = db.query(Job).filter(Job.status == "QUEUED").order_by(Job.created_at.asc()).first()
                if next_job:
                    asyncio.run(process_job(next_job.id))
        except Exception as e:
            logger.error(f"Loop error: {str(e)}")
        finally:
            db.close()
        time.sleep(3)

if __name__ == "__main__":
    main_loop()
