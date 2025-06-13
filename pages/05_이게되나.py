import streamlit as st
import pandas as pd
import numpy as np
import time
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

# --- 1) 데이터 로드 및 전처리 캐시 ---
@st.cache_data
def load_data():
    df = pd.read_csv('enhanced_student_habits_performance_dataset.csv')
    numeric_cols = [
        'age','study_hours_per_day','social_media_hours','netflix_hours',
        'attendance_percentage','sleep_hours','exercise_frequency',
        'screen_time','parental_support_level','motivation_level','exam_anxiety_score'
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
    st.title('🔍 학업 성취도 유사도 조회 & 결과 🚀')

    # 데이터 및 모델 준비
    df = load_data()
    numeric_features = [
        'age','study_hours_per_day','social_media_hours','netflix_hours',
        'attendance_percentage','sleep_hours','exercise_frequency',
        'screen_time','parental_support_level','motivation_level','exam_anxiety_score'
    ]
    categorical_features = [
        'gender','part_time_job','diet_quality',
        'parental_education_level','extracurricular_participation',
        'dropout_risk','study_environment','access_to_tutoring',
        'family_income_range','learning_style'
    ]
    all_feats = numeric_features + categorical_features
    pre = create_preprocessor(df, numeric_features, categorical_features)
    X_all = transform_dataset(df, pre, all_feats)

    # 한글 라벨 매핑
    labels = {
        'age': '나이',
        'study_hours_per_day': '하루 공부 시간(시간)',
        'social_media_hours': '하루 소셜 미디어 사용(시간)',
        'netflix_hours': '하루 넷플릭스 시청(시간)',
        'attendance_percentage': '출석률(%)',
        'sleep_hours': '하루 수면 시간(시간)',
        'exercise_frequency': '운동 빈도(주당)',
        'screen_time': '화면 사용 시간(시간)',
        'parental_support_level': '부모 지원 수준',
        'motivation_level': '동기 수준',
        'exam_anxiety_score': '시험 불안 점수',
        'gender': '성별',
        'part_time_job': '아르바이트 여부',
        'diet_quality': '식단 질',
        'parental_education_level': '부모 교육 수준',
        'extracurricular_participation': '과외 활동 여부',
        'dropout_risk': '퇴학 위험 여부',
        'study_environment': '학습 환경 유형',
        'access_to_tutoring': '튜터링 접근성',
        'family_income_range': '가족 소득 범위',
        'learning_style': '학습 스타일'
    }

    # 세션 초기화
    if 'show_result' not in st.session_state:
        st.session_state.show_result = False

    # 사이드바 입력 영역
    st.sidebar.header('🎯 학생 특성 입력')
    user_input = {}
    for feat in numeric_features:
        mn, mx, md = float(df[feat].min()), float(df[feat].max()), float(df[feat].mean())
        user_input[feat] = st.sidebar.slider(labels[feat], mn, mx, md)
    for feat in categorical_features:
        options = df[feat].dropna().unique().tolist()
        user_input[feat] = st.sidebar.selectbox(labels[feat], options)
    if st.sidebar.button('🔍 조회하기'):
        st.session_state.user_input = user_input
        st.session_state.show_result = True

    # 메인 결과 영역
    st.header('✨ 결과')
    if st.session_state.show_result:
        placeholder = st.empty()
        for i in range(3, 0, -1):
            placeholder.info(f"⏳ {i}초 후 결과 표시 중...")
            time.sleep(1)
        placeholder.empty()
        ui = st.session_state.user_input
        inp_df = pd.DataFrame([ui])
        inp_df[numeric_features] = inp_df[numeric_features].apply(pd.to_numeric, errors='coerce')
        inp_df[categorical_features] = inp_df[categorical_features].astype(str)
        X_in = transform_dataset(inp_df, pre, all_feats)
        dists = np.linalg.norm(X_all - X_in, axis=1)
        idx = np.argmin(dists)
        sim = df.iloc[idx]
        st.subheader('👤 가장 유사한 학생 정보')
        st.json({
            '출석률(%)': sim['attendance_percentage'],
            '시험 불안 점수': int(sim['exam_anxiety_score']),
            '최종 시험 점수': int(sim['exam_score'])
        })
        st.success(f"🎉 예상 점수: {int(sim['exam_score'])}점 🎉")
    else:
        st.info('▶️ 사이드바에서 특성을 입력 후, [🔍 조회하기] 버튼을 눌러주세요.')

if __name__ == '__main__':
    main()
