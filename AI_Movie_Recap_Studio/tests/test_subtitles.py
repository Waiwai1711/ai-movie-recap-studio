import os
from app.services.subtitle_service import SubtitleService

def test_srt_generation(tmp_path):
    out_file = str(tmp_path / "test.srt")
    sentences = ["မင်္ဂလာပါ", "ဇာတ်လမ်းစတင်ပါပြီ"]
    durs = [2.5, 3.0]
    content = SubtitleService.generate_srt(sentences, durs, out_file)
    assert "00:00:00,000 --> 00:00:02,500" in content
    assert "မင်္ဂလာပါ" in content
