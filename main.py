import streamlit as st
import pandas as pd

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
            df["파일명"] = uploaded_file.name  # 어떤 파일에서 왔는지 추적용
            dfs.append(df)
        except Exception as e:
            st.error(f"{uploaded_file.name} 읽기 실패: {e}")

    if dfs:
        merged_df = pd.concat(dfs, ignore_index=True)
        st.success(f"{len(dfs)}개의 파일을 성공적으로 합쳤습니다!")
        st.dataframe(merged_df)

        # 다운로드 링크 제공
        @st.cache_data
        def convert_df(df):
            return df.to_excel(index=False, engine='openpyxl')

        excel_data = convert_df(merged_df)
        st.download_button(
            label="엑셀로 다운로드",
            data=excel_data,
            file_name="합쳐진_파일.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
