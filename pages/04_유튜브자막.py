import os
import subprocess
import json
import tempfile
import datetime
from typing import Optional

import streamlit as st
import whisper
import imageio_ffmpeg as ffmpeg_io  # imageio-ffmpeg 로 ffmpeg 바이너리 확보

# 1) imageio-ffmpeg 가 내려받은 ffmpeg 경로 얻기
ffmpeg_path = ffmpeg_io.get_ffmpeg_exe()

# 2) Whisper 내부가 shutil.which("ffmpeg")로 찾기 때문에 PATH 에 추가
ffmpeg_dir = os.path.dirname(ffmpeg_path)
os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

# (선택) Whisper 에서 사용하는 ffmpeg 경로 환경변수 설정
os.environ["FFMPEG_BINARY"] = ffmpeg_path

def format_time(seconds: float) -> str:
    """SRT 타임코드 형식 HH:MM:SS,mmm"""
    td = datetime.timedelta(seconds=seconds)
    total = td.total_seconds()
    h = int(total // 3600)
    m = int((total % 3600) // 60)
    s = int(total % 60)
    ms = int((total - int(total)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def get_subtitles(url: str) -> Optional[str]:
    """yt-dlp 메타 → 수동 자막(.vtt) 다운로드"""
    proc = subprocess.run(
        ["yt-dlp", "-J", url],
        capture_output=True, text=True
    )
    if proc.returncode != 0:
        st.error("메타데이터를 가져오는 데 실패했습니다.")
        return None
    meta = json.loads(proc.stdout)
    subs = meta.get("subtitles", {})
    if not subs:
        return None

    lang, _ = next(iter(subs.items()))
    tmp_vtt = tempfile.NamedTemporaryFile(suffix=".vtt", delete=False).name
    dl = subprocess.run([
        "yt-dlp", url,
        "--skip-download",
        "--write-sub",
        "--sub-lang", lang,
        "--sub-format", "vtt",
        "-o", tmp_vtt
    ])
    if dl.returncode == 0 and os.path.exists(tmp_vtt):
        return tmp_vtt

    st.error("기존 자막 다운로드에 실패했습니다.")
    return None

def convert_sub_to_txt(sub_path: str) -> str:
    """.vtt/.srt → 순수 텍스트(.txt) 추출"""
    txt_path = sub_path.rsplit(".", 1)[0] + ".txt"
    lines = []
    with open(sub_path, "r", encoding="utf-8") as f:
        for line in f:
            t = line.strip()
            if not t or t.isdigit() or "-->" in t:
                continue
            lines.append(t)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return txt_path

def transcribe_with_whisper(audio_path: str) -> str:
    """Whisper 로 음성인식 → .srt 생성"""
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)

    srt_path = audio_path + ".srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(result["segments"], start=1):
            start = format_time(seg["start"])
            end   = format_time(seg["end"])
            text  = seg["text"].strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    return srt_path

def main():
    st.title("📥 유튜브 자막(.txt) 다운로드 / Whisper 자막 생성(.txt)")
    url = st.text_input("유튜브 영상 URL을 입력하세요")

    if st.button("자막 가져오기"):
        if not url:
            st.warning("URL을 입력해주세요.")
            return

        # 1) 수동 자막 시도
        with st.spinner("기존 자막을 검색 중입니다..."):
            sub = get_subtitles(url)

        if sub:
            txt = convert_sub_to_txt(sub)
            st.success("기존 자막 다운로드 완료!")
            data = open(txt, "rb").read()
            st.download_button("자막 다운로드 (.txt)", data, os.path.basename(txt), "text/plain")
        else:
            # 2) 없으면 Whisper 음성인식
            st.info("기존 자막이 없어 Whisper로 생성합니다...")
            audio_tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
            with st.spinner("오디오 다운로드 중..."):
                subprocess.run(["yt-dlp", url, "-f", "bestaudio", "-o", audio_tmp], check=True)

            with st.spinner("Whisper 음성인식 중..."):
                srt = transcribe_with_whisper(audio_tmp)

            txt = convert_sub_to_txt(srt)
            st.success("Whisper 자막 생성 완료!")
            data = open(txt, "rb").read()
            st.download_button("생성된 자막 다운로드 (.txt)", data, os.path.basename(txt), "text/plain")

if __name__ == "__main__":
    main()
