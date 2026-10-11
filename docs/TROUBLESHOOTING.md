# Troubleshooting Guide

1. **FFmpeg Error**: Ensure `ffmpeg` and `ffprobe` are installed via `sudo apt install ffmpeg`.
2. **Burmese Font Issue**: Install `fonts-noto-core` and `fonts-sil-padauk`.
3. **Database Lock**: SQLite is configured in WAL mode; ensure permissions on `./storage`.
