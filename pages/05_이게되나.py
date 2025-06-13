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
    st.title('🔍 학업 성취도 유사도 조회 & 결과 🚀')

    # 데이터 및 모델 준비
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

    # 한글 라벨 매핑
    labels = {
        'age': '나이',
        'gender': '성별',
        'major': '전공',
        'study_hours_per_day': '하루 공부 시간(시간)',
        'social_media_hours': '하루 소셜 미디어 사용(시간)',
        'netflix_hours': '하루 넷플릭스 시청(시간)',
        'part_time_job': '아르바이트 여부',
        'attendance_percentage': '출석률(%)',
        'sleep_hours': '하루 수면 시간(시간)',
        'diet_quality': '식단 질',
        'exercise_frequency': '운동 빈도(주당)',
        'parental_education_level': '부모 교육 수준',
        'internet_quality': '인터넷 품질',
        'mental_health_rating': '정신 건강 (1-10)',
        'extracurricular_participation': '과외 활동 여부',
        'previous_gpa': '이전 학기 GPA',
        'semester': '학기',
        'stress_level': '스트레스 수준',
        'dropout_risk': '퇴학 위험 여부',
        'social_activity': '사회 활동 수준',
        'screen_time': '화면 사용 시간(시간)',
        'study_environment': '학습 환경 유형',
        'access_to_tutoring': '튜터링 접근성',
        'family_income_range': '가족 소득 범위',
        'parental_support_level': '부모 지원 수준',
        'motivation_level': '동기 수준',
        'exam_anxiety_score': '시험 불안 점수',
        'learning_style': '학습 스타일',
        'time_management_score': '시간 관리 점수'
    }

    # 상태 초기화
    if 'show_result' not in st.session_state:
        st.session_state.show_result = False

    # 레이아웃: 좌우 컬럼
    col1, col2 = st.columns(2)

    with col1:
        st.header('🎯 학생 특성 입력')
        user_input = {}
        for f in num_feats:
            mn, mx, md = float(df[f].min()), float(df[f].max()), float(df[f].mean())
            if f == 'semester':
                user_input[f] = st.slider(labels[f], int(mn), int(mx), int(round(md)))
            else:
                user_input[f] = st.slider(labels[f], mn, mx, md)
        for f in cat_feats:
            options = df[f].dropna().unique().tolist()
            user_input[f] = st.selectbox(labels[f], options)
        if st.button('🔍 조회하기'):
            st.session_state.user_input = user_input
            st.session_state.show_result = True

    with col2:
        st.header('✨ 결과 공간')
        if st.session_state.show_result:
            placeholder = st.empty()
            for i in range(3, 0, -1):
                placeholder.info(f"⏳ {i}초 후 결과 표시 중...")
                time.sleep(1)
            placeholder.empty()
            ui = st.session_state.user_input
            inp_df = pd.DataFrame([ui])
            inp_df[num_feats] = inp_df[num_feats].apply(pd.to_numeric, errors='coerce')
            inp_df[cat_feats] = inp_df[cat_feats].astype(str)
            X_in = transform_dataset(inp_df, pre, all_feats)
            dists = np.linalg.norm(X_all - X_in, axis=1)
            idx = np.argmin(dists)
            sim = df.iloc[idx]
            st.subheader('👤 가장 유사한 학생 정보')
            st.json({
                '이전 GPA': sim['previous_gpa'],
                '출석률(%)': sim['attendance_percentage'],
                '학기': int(sim['semester']),
                '스트레스 수준': sim['stress_level'],
                '시험 불안 점수': int(sim['exam_anxiety_score']),
                '최종 시험 점수': int(sim['exam_score'])
            })
            st.success(f"🎉 예상 점수: {int(sim['exam_score'])}점 🎉")
        else:
            st.info('▶️ 왼쪽에서 특성을 입력 후, [🔍 조회하기] 버튼을 눌러주세요.')

if __name__ == '__main__':
    main()
