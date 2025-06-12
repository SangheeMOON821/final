# streamlit_app.py

import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# 데이터 로드
@st.cache_data
def load_data():
    return pd.read_csv("enhanced_student_habits_performance_dataset.csv")

df = load_data()

st.title("📈 습관 조절을 통한 학업 성취도 예측")

# 사전 처리
df_model = df.copy()

# 범주형 라벨 인코딩
categorical_cols = df_model.select_dtypes(include="object").columns.tolist()
label_encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    df_model[col] = le.fit_transform(df_model[col])
    label_encoders[col] = le

# feature와 target 설정
target = "exam_score"
X = df_model.drop(columns=["student_id", target])
y = df_model[target]

# 모델 학습
model = LinearRegression()
model.fit(X, y)

# 사용자 입력 UI
st.sidebar.header("🔧 변수 조정 (모델 입력값)")

input_data = {}
for col in X.columns:
    if df_model[col].dtype == "float64" or df_model[col].dtype == "int64":
        min_val = float(df_model[col].min())
        max_val = float(df_model[col].max())
        mean_val = float(df_model[col].mean())
        input_data[col] = st.sidebar.slider(col, min_value=min_val, max_value=max_val, value=mean_val)
    else:
        options = label_encoders[col].classes_.tolist()
        selected_option = st.sidebar.selectbox(col, options)
        input_data[col] = label_encoders[col].transform([selected_option])[0]

# 예측
input_df = pd.DataFrame([input_data])
predicted_score = model.predict(input_df)[0]

st.subheader("🎯 예측된 시험 점수")
st.metric(label="예측된 exam_score", value=f"{predicted_score:.2f} 점")

# 회귀모델 중요 변수 시각화
st.subheader("📊 회귀 계수(변수 영향도)")
coef_df = pd.DataFrame({
    "Feature": X.columns,
    "Coefficient": model.coef_
}).sort_values(by="Coefficient", key=abs, ascending=False)

st.bar_chart(coef_df.set_index("Feature"))
