import streamlit as st
import pandas as pd
from io import BytesIO

st.title("엑셀 파일 합치기")

uploaded_files = st.file_uploader(
    "엑셀 파일을 여러 개 업로드하세요", 
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

if uploaded_files:
    dfs = []
    for uploaded_file in uploaded_files:
        try:
            df = pd.read_excel(uploaded_file)
            df["파일명"] = uploaded_file.name
            dfs.append(df)
        except Exception as e:
            st.error(f"{uploaded_file.name} 읽기 실패: {e}")

    if dfs:
        merged_df = pd.concat(dfs, ignore_index=True)
        st.success(f"{len(dfs)}개의 파일을 성공적으로 합쳤습니다!")
        st.dataframe(merged_df)

        # 엑셀 다운로드용 BytesIO로 변환
        def to_excel_bytes(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            output.seek(0)
            return output

        excel_data = to_excel_bytes(merged_df)
        st.download_button(
            label="엑셀로 다운로드",
            data=excel_data,
            file_name="합쳐진_파일.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
