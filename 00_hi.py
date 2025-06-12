
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

st.title("학생 습관과 학업 성취도 분석")

# 사이드바 필터
st.sidebar.header("필터")
selected_major = st.sidebar.multiselect("전공 선택", options=df["major"].unique(), default=df["major"].unique())
selected_gender = st.sidebar.multiselect("성별 선택", options=df["gender"].unique(), default=df["gender"].unique())

filtered_df = df[(df["major"].isin(selected_major)) & (df["gender"].isin(selected_gender))]

st.subheader("공부 시간 vs 시험 점수")
fig1, ax1 = plt.subplots()
sns.scatterplot(data=filtered_df, x="study_hours_per_day", y="exam_score", hue="gender", ax=ax1)
st.pyplot(fig1)

st.subheader("수면 시간 vs 시험 점수")
fig2, ax2 = plt.subplots()
sns.scatterplot(data=filtered_df, x="sleep_hours", y="exam_score", hue="gender", ax=ax2)
st.pyplot(fig2)

st.subheader("SNS 사용 시간 vs 시험 점수")
fig3, ax3 = plt.subplots()
sns.scatterplot(data=filtered_df, x="social_media_hours", y="exam_score", hue="gender", ax=ax3)
st.pyplot(fig3)

st.subheader("학습 환경별 평균 시험 점수")
avg_scores = filtered_df.groupby("study_environment")["exam_score"].mean().sort_values()
st.bar_chart(avg_scores)

# 데이터 확인
with st.expander("원본 데이터 보기"):
    st.dataframe(filtered_df)
