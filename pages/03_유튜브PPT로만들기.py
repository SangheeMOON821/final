import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from pptx import Presentation
from pptx.util import Inches
from urllib.parse import urlparse, parse_qs
import textwrap
import os

def extract_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed_url.query).get("v", [None])[0]
    elif parsed_url.hostname == "youtu.be":
        return parsed_url.path[1:]
    return None

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko", "en"])
        return " ".join([t["text"] for t in transcript])
    except Exception as e:
        return None

def summarize_text(text, max_sentences=5):
    # 아주 단순한 요약: 문장 분리 후 앞부분 몇 개만 추출
    sentences = text.split(". ")
    return ". ".join(sentences[:max_sentences]) + ("." if sentences else "")

def create_ppt(youtube_url, summary_chunks):
    prs = Presentation()
    
    # 첫 슬라이드 - 링크
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "YouTube 영상 요약"
    subtitle.text = youtube_url

    # 내용 슬라이드
    for i, chunk in enumerate(summary_chunks):
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        content = slide.placeholders[1]
        title.text = f"요약 {i+1}"
        content.text = chunk

    return prs

def split_summary(summary, max_length=500):
    # ppt 슬라이드 하나당 적당한 길이로 분할
    return textwrap.wrap(summary, width=max_length)

st.title("📺 유튜브 영상으로 PPT 요약 만들기")

youtube_url = st.text_input("유튜브 링크를 입력하세요:")

if youtube_url:
    video_id = extract_video_id(youtube_url)
    if not video_id:
        st.error("유효한 유튜브 링크가 아닙니다.")
    else:
        st.info("자막을 가져오는 중입니다...")
        transcript_text = get_transcript(video_id)

        if transcript_text is None:
            st.error("자막을 불러올 수 없습니다. 공개된 자막이 있는 영상인지 확인해주세요.")
        else:
            st.success("자막 가져오기 성공!")
            summary = summarize_text(transcript_text, max_sentences=15)
            summary_chunks = split_summary(summary)

            prs = create_ppt(youtube_url, summary_chunks)

            output_path = "youtube_summary.pptx"
            prs.save(output_path)

            with open(output_path, "rb") as f:
                st.download_button(
                    label="📥 PPT 다운로드",
                    data=f,
                    file_name="youtube_summary.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                )

            os.remove(output_path)
