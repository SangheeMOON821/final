# streamlit_app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 데이터 불러오기
@st.cache_data
def load_data():
    return pd.read_csv("enhanced_student_habits_performance_dataset.csv")

df = load_data()

st.title("📊 학생 습관과 학업 성취도 분석")

# 사이드바 필터
st.sidebar.header("🔎 필터")
selected_major = st.sidebar.multiselect("전공 선택", options=df["major"].unique(), default=df["major"].unique())
selected_gender = st.sidebar.multiselect("성별 선택", options=df["gender"].unique(), default=df["gender"].unique())

filtered_df = df[(df["major"].isin(selected_major)) & (df["gender"].isin(selected_gender))]

# 분석할 변수 선택
st.subheader("변수별 학업 성취도 시각화")

# 학습 습관/요인 변수 목록 자동 추출 (수치형 + 범주형 일부)
target_col = "exam_score"
exclude_cols = ["student_id", "exam_score", "major", "gender"]
variables = [col for col in df.columns if col not in exclude_cols]

selected_var = st.selectbox("비교할 변수 선택", variables)

# 시각화
if pd.api.types.is_numeric_dtype(df[selected_var]):
    st.write(f"📈 **{selected_var}** vs **시험 점수 (exam_score)**")
    fig, ax = plt.subplots()
    sns.scatterplot(data=filtered_df, x=selected_var, y="exam_score", hue="gender", ax=ax)
    st.pyplot(fig)
else:
    st.write(f"📊 **{selected_var}**별 평균 시험 점수")
    grouped = filtered_df.groupby(selected_var)["exam_score"].mean().sort_values()
    st.bar_chart(grouped)

# 상관계수 히트맵 옵션
