
```python
import os
import subprocess
import json
import tempfile
import datetime

import streamlit as st
import whisper
import imageio_ffmpeg as ffmpeg_io  # <- 추가

# imageio-ffmpeg 가 내려받은 바이너리 경로를 Whisper가 사용하도록 환경변수에 설정
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

def get_subtitles(url: str) -> str | None:
  # 1) 메타데이터 JSON 가져오기
  meta_proc = subprocess.run(
      ["yt-dlp", "-J", url],
      capture_output=True, text=True
  )
  if meta_proc.returncode != 0:
      st.error("메타데이터를 가져오는 데 실패했습니다.")
      return None
  meta = json.loads(meta_proc.stdout)

  # 2) 수동 자막(subtitles)이 있으면 첫 언어 트랙으로 다운로드 (.vtt)
  subs = meta.get("subtitles", {})
  if subs:
      lang, _ = next(iter(subs.items()))
      tmp_vtt = tempfile.NamedTemporaryFile(suffix=".vtt", delete=False).name
      dl_proc = subprocess.run([
          "yt-dlp", url,
          "--skip-download",
          "--write-sub",
          "--sub-lang", lang,
          "--sub-format", "vtt",
          "-o", tmp_vtt
      ])
      if dl_proc.returncode == 0 and os.path.exists(tmp_vtt):
          return tmp_vtt
      else:
          st.error("기존 자막 다운로드에 실패했습니다.")
  return None

def convert_sub_to_txt(sub_path: str) -> str:
  """
  .vtt 또는 .srt 파일에서 텍스트만 추출해 .txt로 저장
  """
  txt_path = sub_path.rsplit(".", 1)[0] + ".txt"
  lines = []
  with open(sub_path, "r", encoding="utf-8") as f:
      for line in f:
          line = line.strip()
          # 숫자 인덱스나 시간코드(--> 포함) 제외
          if not line or line.isdigit() or "-->" in line:
              continue
          lines.append(line)
  with open(txt_path, "w", encoding="utf-8") as f:
      f.write("\n".join(lines))
  return txt_path

def transcribe_with_whisper(audio_path: str) -> str:
  """
  Whisper로 음성 인식 후 .srt 파일 생성.
  imageio-ffmpeg 로 확보된 ffmpeg 바이너리를 사용하므로 FileNotFoundError가 발생하지 않습니다.
  """
  model = whisper.load_model("base")
  result = model.transcribe(audio_path)

  # .srt 파일 생성
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
          st.warning("먼저 URL을 입력해주세요.")
          return

      # 1) 기존 자막 확인
      with st.spinner("기존 자막을 검색 중입니다..."):
          sub_file = get_subtitles(url)

      if sub_file:
          # .vtt → .txt 변환
          txt_file = convert_sub_to_txt(sub_file)
          st.success("기존 자막을 찾아 다운로드했습니다.")
          txt_bytes = open(txt_file, "rb").read()
          st.download_button(
              label="자막 다운로드 (.txt)",
              data=txt_bytes,
              file_name=os.path.basename(txt_file),
              mime="text/plain"
          )
      else:
          # 2) 자막이 없으면 Whisper로 생성
          st.info("자막이 없어 Whisper로 생성합니다. (처리에 시간이 소요될 수 있습니다)")
          # 오디오만 다운로드
          audio_tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
          with st.spinner("오디오 다운로드 중..."):
              subprocess.run([
                  "yt-dlp", url,
                  "-f", "bestaudio",
                  "-o", audio_tmp
              ], check=True)

          with st.spinner("Whisper로 자막 생성 중..."):
              srt_file = transcribe_with_whisper(audio_tmp)

          # .srt → .txt 변환
          txt_file = convert_sub_to_txt(srt_file)
          st.success("Whisper 자막 생성 완료!")
          txt_bytes = open(txt_file, "rb").read()
          st.download_button(
              label="생성된 자막 다운로드 (.txt)",
              data=txt_bytes,
              file_name=os.path.basename(txt_file),
              mime="text/plain"
          )

if __name__ == "__main__":
  main()
