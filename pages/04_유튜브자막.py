import os
import subprocess
import json
import tempfile
import datetime
from typing import Optional

import streamlit as st
import whisper
import imageio_ffmpeg as ffmpeg_io  # imageio-ffmpeg 으로 ffmpeg 바이너리 확보

# Whisper가 사용할 ffmpeg 경로 설정
os.environ["FFMPEG_BINARY"] = ffmpeg_io.get_ffmpeg_exe()

def format_time(seconds: float) -> str:
    """SRT 타임코드 형식으로 변경: HH:MM:SS,mmm"""
    td = datetime.timedelta(seconds=seconds)
    total_seconds = td.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    secs = int(total_seconds % 60)
    millis = int((total_seconds - int(total_seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def get_subtitles(url: str) -> Optional[str]:
    """
    yt-dlp 메타데이터에서 자막이 있는지 확인하고,
    있으면 .vtt 파일로 다운로드하여 경로를 반환합니다.
    """
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
    """
    .vtt 또는 .srt 파일에서 번호와 시간코드를 제외한
    순수 텍스트만 추출해 .txt로 저장하고 경로를 반환합니다.
    """
    txt_path = sub_path.rsplit(".", 1)[0] + ".txt"
    lines = []

    with open(sub_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.isdigit() or "-->" in line:
                continue
            lines.append(line)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return txt_path

def transcribe_with_whisper(audio_path: str) -> str:
    """
    Whisper 모델로 음성인식 후 .srt 파일을 생성하여 경로를 반환합니다.
    imageio-ffmpeg로 확보된 바이너리를 사용하므로 FileNotFoundError가 없습니다.
    """
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

        with st.spinner("기존 자막을 검색 중입니다..."):
            sub_file = get_subtitles(url)

        if sub_file:
            txt_file = convert_sub_to_txt(sub_file)
            st.success("기존 자막 다운로드 완료!")
            data = open(txt_file, "rb").read()
            st.download_button(
                label="자막 다운로드 (.txt)",
                data=data,
                file_name=os.path.basename(txt_file),
                mime="text/plain"
            )
        else:
            st.info("자막이 없어 Whisper로 생성합니다. 잠시만 기다려주세요...")
            audio_tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name

            with st.spinner("오디오 다운로드 중..."):
                subprocess.run([
                    "yt-dlp", url,
                    "-f", "bestaudio",
                    "-o", audio_tmp
                ], check=True)

            with st.spinner("Whisper 음성인식 중..."):
                srt_file = transcribe_with_whisper(audio_tmp)

            txt_file = convert_sub_to_txt(srt_file)
            st.success("Whisper 자막 생성 완료!")
            data = open(txt_file, "rb").read()
            st.download_button(
                label="생성된 자막 다운로드 (.txt)",
                data=data,
                file_name=os.path.basename(txt_file),
                mime="text/plain"
            )

if __name__ == "__main__":
    main()
