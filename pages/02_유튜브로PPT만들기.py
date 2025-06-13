import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from pptx import Presentation
from pptx.util import Inches
import re
import tempfile
import os

def extract_video_id(url):
    """유튜브 URL에서 비디오 ID 추출"""
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    return match.group(1) if match else None

def get_transcript(video_id):
    """유튜브 자막 추출"""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item["text"] for item in transcript])
    except TranscriptsDisabled:
        return None

def summarize_text(text, max_chars=800):
    """긴 자막 텍스트를 일정 길이 단위로 나눠 요약"""
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def create_ppt(youtube_url, summaries):
    """PPT 파일 생성"""
    prs = Presentation()

    # 첫 슬라이드 (유튜브 링크)
    slide_layout = prs.slide_layouts[0]  # 타이틀 슬라이드
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = "YouTube Summary Presentation"
    slide.placeholders[1].text = f"Link: {youtube_url}"

    # 요약 슬라이드들
    content_layout = prs.slide_layouts[1]  # 제목 + 콘텐츠
    for idx, summary in enumerate(summaries, start=1):
        slide = prs.slides.add_slide(content_layout)
        slide.shapes.title.text = f"요약 {idx}"
        slide.placeholders[1].text = summary

    # 임시 파일로 저장
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx")
    prs.save(tmp_file.name)
    return tmp_file.name

# ---------------- Streamlit UI ----------------
st.title("YouTube 영상 요약 PPT 생성기")

youtube_url = st.text_input("유튜브 링크를 입력하세요")

if st.button("PPT 만들기"):
    if not youtube_url:
        st.warning("유튜브 링크를 입력해주세요.")
    else:
        video_id = extract_video_id(youtube_url)
        if not video_id:
            st.error("유효한 유튜브 링크가 아닙니다.")
        else:
            with st.spinner("자막 추출 중..."):
                transcript = get_transcript(video_id)

            if transcript is None:
                st.error("이 영상에는 자막이 없거나, 접근할 수 없습니다.")
            else:
                with st.spinner("내용 요약 및 PPT 생성 중..."):
                    summaries = summarize_text(transcript)
                    ppt_file_path = create_ppt(youtube_url, summaries)

                with open(ppt_file_path, "rb") as f:
                    st.success("PPT 생성 완료!")
                    st.download_button(
                        label="PPT 다운로드",
                        data=f,
                        file_name="youtube_summary.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                    )
                os.remove(ppt_file_path)
