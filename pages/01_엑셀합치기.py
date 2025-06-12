import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.title("엑셀 파일 → 시트 병합기")

uploaded_files = st.file_uploader(
    "엑셀 파일을 여러 개 업로드하세요", 
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

if uploaded_files:
    def sanitize_sheet_name(name):
        # Excel 시트명은 최대 31자, 특수문자 불가
        name = re.sub(r'[:\\/?*\[\]]', '', name)
        return name[:31]

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for uploaded_file in uploaded_files:
            try:
                df = pd.read_excel(uploaded_file)
                sheet_name = sanitize_sheet_name(uploaded_file.name.replace('.xlsx', '').replace('.xls', ''))
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            except Exception as e:
                st.error(f"{uploaded_file.name} 읽기 실패: {e}")
        writer.save()
    output.seek(0)

    st.success(f"{len(uploaded_files)}개의 파일이 하나의 엑셀 파일로 시트 병합되었습니다!")

    st.download_button(
        label="엑셀로 다운로드",
        data=output,
        file_name="시트별_병합된_파일.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
