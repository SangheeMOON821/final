# 필요한 라이브러리 설치:
# pip install streamlit youtube-transcript-api

import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from urllib.parse import urlparse, parse_qs

# YouTube URL에서 video_id 추출
def extract_video_id(url):
    parsed = urlparse(url)
    if parsed.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed.query).get("v", [None])[0]
    if parsed.hostname == "youtu.be":
        return parsed.path[1:]
    return None

# 공개 자막(스크립트) 가져오기
def get_transcript(video_id):
    try:
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        # 한국어, 영어 순으로 시도
        transcript = transcripts.find_transcript(['ko', 'en'])
        segments = transcript.fetch()
        # 텍스트만 합치기
        text = "\n".join([seg['text'] for seg in segments])
        return text
    except TranscriptsDisabled:
        return None
    except Exception:
        return None

# Streamlit 앱
st.title("📝 YouTube 스크립트 가져오기")
youtube_url = st.text_input("유튜브 링크를 입력하세요:")

if youtube_url:
    vid = extract_video_id(youtube_url)
    if not vid:
        st.error("❌ 유효한 유튜브 링크가 아닙니다.")
    else:
        st.info("자막(스크립트) 불러오는 중...")
        transcript = get_transcript(vid)
        if transcript:
            st.success("✅ 스크립트 가져오기 성공!")
            # 스크립트 출력
            st.text_area("스크립트", transcript, height=300)
            # 텍스트 파일로 다운로드
            st.download_button(
                label="📥 스크립트 다운로드",
                data=transcript,
                file_name=f"{vid}_transcript.txt",
                mime="text/plain"
            )
        else:
            st.error("❌ 공개 자막(스크립트)을 가져올 수 없습니다.")
