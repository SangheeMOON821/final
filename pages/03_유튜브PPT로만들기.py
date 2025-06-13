import streamlit as st
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptAvailable
from urllib.parse import urlparse, parse_qs
import whisper
import os

# 1) 유튜브 video_id 추출
def extract_video_id(url):
    parsed = urlparse(url)
    if parsed.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed.query).get("v", [None])[0]
    if parsed.hostname == "youtu.be":
        return parsed.path[1:]
    return None

# 2) 공개 자막 가져오기
def get_youtube_transcript(video_id):
    try:
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        tr = transcripts.find_transcript(['ko','en'])
        return " ".join([seg["text"] for seg in tr.fetch()])
    except (TranscriptsDisabled, NoTranscriptAvailable):
        return None
    except:
        return None

# 3) Whisper로 음성 다운로드 및 인식
def download_audio(video_url, fname="audio.mp4"):
    yt = YouTube(video_url)
    stream = yt.streams.filter(only_audio=True).first()
    return stream.download(filename=fname)

def transcribe_whisper(audio_path):
    model = whisper.load_model("base")
    res = model.transcribe(audio_path, language='ko')
    return res["text"]

# 4) 스크립트를 n개 섹션으로 분할
def split_to_sections(text, n):
    sentences = [s.strip() for s in text.split('. ') if s]
    size = len(sentences) // n
    sections = []
    for i in range(n):
        start = i*size
        end = (i+1)*size if i < n-1 else len(sentences)
        chunk = ". ".join(sentences[start:end])
        if not chunk.endswith("."):
            chunk += "."
        sections.append(chunk)
    return sections

# 5) 각 섹션에서 한 문장으로 제목 생성
def summarize_title(chunk):
    # 맨 앞 문장을 제목으로 사용하거나, 간단 요약
    first = chunk.split(".")[0]
    return first[:50] + "..." if len(first) > 50 else first

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
        st.success("Whisper 인식 완료!")

    # 섹션 개수 선택
    n_sec = st.sidebar.number_input("섹션 개수", min_value=2, max_value=10, value=5, step=1)

    # 분할 & 제목 생성
    secs = split_to_sections(script, n_sec)
    titles = [summarize_title(s) for s in secs]

    # 사이드바에 목차 표시
    choice = st.sidebar.radio("목차", titles)

    # 선택된 섹션 인덱스
    idx = titles.index(choice)

    # 본문에 보여주기
    st.header(choice)
    st.write(secs[idx])

    # 전체 스크립트는 확장(expander)으로
    with st.expander("👉 전체 스크립트 보기"):
        st.write(script)
