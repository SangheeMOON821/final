import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

# --- 1) 데이터 로드 및 전처리 캐시 ---
@st.cache_data
def load_data():
    df = pd.read_csv('enhanced_student_habits_performance_dataset.csv')
    numeric_cols = [
        'age','study_hours_per_day','social_media_hours','netflix_hours',
        'attendance_percentage','sleep_hours','exercise_frequency',
        'internet_quality','mental_health_rating','previous_gpa',
        'semester','stress_level','social_activity','screen_time',
        'parental_support_level','motivation_level','exam_anxiety_score',
        'time_management_score'
    ]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    return df

@st.cache_resource
def create_preprocessor(df, numeric_features, categorical_features):
    df_copy = df[numeric_features + categorical_features].copy()
    df_copy[numeric_features] = df_copy[numeric_features].apply(pd.to_numeric, errors='coerce')
    df_copy[categorical_features] = df_copy[categorical_features].astype(str)
    num_t = StandardScaler()
    cat_t = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    pre = ColumnTransformer([
        ('num', num_t, numeric_features),
        ('cat', cat_t, categorical_features)
    ])
    pre.fit(df_copy)
    return pre

def transform_dataset(df, preprocessor, feature_cols):
    df2 = df[feature_cols].copy()
    num_feats = preprocessor.transformers_[0][2]
    cat_feats = preprocessor.transformers_[1][2]
    df2[num_feats] = df2[num_feats].apply(pd.to_numeric, errors='coerce')
    df2[cat_feats] = df2[cat_feats].astype(str)
    X = preprocessor.transform(df2)
    return np.nan_to_num(X, nan=0.0, posinf=np.inf, neginf=-np.inf)

# --- 앱 시작 ---
def main():
    st.title('📊 학업 성취도 유사도 기반 조회')
    df = load_data()
    num_feats = [
        'age','study_hours_per_day','social_media_hours','netflix_hours',
        'attendance_percentage','sleep_hours','exercise_frequency',
        'internet_quality','mental_health_rating','previous_gpa',
        'semester','stress_level','social_activity','screen_time',
        'parental_support_level','motivation_level','exam_anxiety_score',
        'time_management_score'
    ]
    cat_feats = [
        'gender','major','part_time_job','diet_quality',
        'parental_education_level','extracurricular_participation',
        'dropout_risk','study_environment','access_to_tutoring',
        'family_income_range','learning_style'
    ]
    all_feats = num_feats + cat_feats
    pre = create_preprocessor(df, num_feats, cat_feats)
    X_all = transform_dataset(df, pre, all_feats)

    labels = { ... }  # 기존 라벨 매핑 유지

    # 세션 상태로 화면 전환
    if 'page' not in st.session_state:
        st.session_state.page = 'input'

    if st.session_state.page == 'input':
        st.header('🎯 학생 특성 입력')
        user = {}
        # 스크롤 휠로 조절 가능한 슬라이더
        for f in num_feats:
            mn, mx, md = float(df[f].min()), float(df[f].max()), float(df[f].mean())
            if f == 'semester':
                user[f] = st.slider(labels[f], int(mn), int(mx), int(round(md)))
            else:
                user[f] = st.slider(labels[f], mn, mx, md)
        for f in cat_feats:
            opts = df[f].dropna().unique().tolist()
            user[f] = st.selectbox(labels[f], opts)
        if st.button('🔍 조회하기'):
            st.session_state.user_input = user
            st.session_state.page = 'result'
            st.experimental_rerun()

    else:  # result page
        st.header('✨ 유사 학생 결과')
        ui = st.session_state.user_input
        inp_df = pd.DataFrame([ui])
        inp_df[num_feats] = inp_df[num_feats].apply(pd.to_numeric, errors='coerce')
        inp_df[cat_feats] = inp_df[cat_feats].astype(str)
        X_in = transform_dataset(inp_df, pre, all_feats)
        dist = np.linalg.norm(X_all - X_in, axis=1)
        idx = np.argmin(dist)
        sim = df.iloc[idx]
        st.write({
            '이전 GPA': sim['previous_gpa'],
            '출석률(%)': sim['attendance_percentage'],
            '학기': int(sim['semester']),
            '스트레스 수준': sim['stress_level'],
            '시험 불안': int(sim['exam_anxiety_score']),
            '최종 점수': int(sim['exam_score'])
        })
        st.success(f"🎉 예상 시험 점수: {int(sim['exam_score'])}점 🎉")
        if st.button('🔄 다시 입력하기'):
            st.session_state.page = 'input'
            st.experimental_rerun()

if __name__ == '__main__':
    main()
