# 필요한 라이브러리 설치:
# pip install streamlit pytube youtube-transcript-api openai-whisper yt-dlp
# sudo apt install ffmpeg

import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from urllib.parse import urlparse, parse_qs
import whisper
import yt_dlp
import os

# 1) YouTube URL에서 video_id 추출
def extract_video_id(url):
    parsed = urlparse(url)
    if parsed.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed.query).get("v", [None])[0]
    if parsed.hostname == "youtu.be":
        return parsed.path[1:]
    return None

# 2) 공개 자막 가져오기 (ko, en 우선)
def get_youtube_transcript(video_id):
    try:
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcripts.find_transcript(['ko', 'en'])
        return " ".join([seg["text"] for seg in transcript.fetch()])
    except TranscriptsDisabled:
        return None
    except Exception:
        return None

# 3) 오디오 다운로드 (yt-dlp 사용)
def download_audio(video_url, fname="audio.mp4"):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': fname,
        'quiet': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    return fname

# 4) Whisper로 음성 → 텍스트 변환
def transcribe_whisper(audio_path):
    model = whisper.load_model("base")
    res = model.transcribe(audio_path, language='ko')
    return res["text"]

# 5) 스크립트를 n개 섹션으로 분할
def split_to_sections(text, n):
    sentences = [s.strip() for s in text.split('. ') if s]
    size = max(1, len(sentences) // n)
    sections = []
    for i in range(n):
        start = i * size
        end = (i + 1) * size if i < n - 1 else len(sentences)
        chunk = ". ".join(sentences[start:end])
        if not chunk.endswith("."):
            chunk += "."
        sections.append(chunk)
    return sections

# 6) 각 섹션의 제목 생성 (첫 문장 기반)
def summarize_title(chunk):
    first = chunk.split(".")[0]
    return (first[:50] + "...") if len(first) > 50 else first

# Streamlit UI
st.title("📑 YouTube 스크립트 구조화 뷰어")

youtube_url = st.text_input("유튜브 링크를 입력하세요:")

if youtube_url:
    vid = extract_video_id(youtube_url)
    if not vid:
        st.error("❌ 유효한 유튜브 링크가 아닙니다.")
        st.stop()

    st.info("자막 확인 중…")
    script = get_youtube_transcript(vid)

    if script is None:
        st.warning("자막 없음 → Whisper로 인식 중…")
        audio_file = download_audio(youtube_url)
        script = transcribe_whisper(audio_file)
        os.remove(audio_file)
        st.success("✅ Whisper 인식 완료!")

    # 사이드바: 섹션 개수 선택
    n_sec = st.sidebar.number_input("섹션 개수", min_value=2, max_value=10, value=5, step=1)

    # 스크립트를 섹션별로 분할하고 제목 생성
    secs = split_to_sections(script, n_sec)
    titles = [summarize_title(s) for s in secs]

    # 사이드바에 목차 표시
    choice = st.sidebar.radio("목차", titles)
    idx = titles.index(choice)

    # 선택된 섹션 내용 출력
    st.header(choice)
    st.write(secs[idx])

    # 전체 스크립트는 확장 영역으로 제공
    with st.expander("👉 전체 스크립트 보기"):
        st.write(script)
