# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# 1) 캐시된 데이터 로드
@st.cache_data
def load_data():
    df = pd.read_csv('enhanced_student_habits_performance_dataset.csv')
    return df

# 2) 캐시된 전처리 파이프라인 생성
@st.cache_resource
def create_preprocessor(df, numeric_features, categorical_features):
    num_transformer = StandardScaler()
    cat_transformer = OneHotEncoder(handle_unknown='ignore', sparse=False)

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_transformer, numeric_features),
            ('cat', cat_transformer, categorical_features)
        ]
    )
    # 전체 데이터로 fit
    preprocessor.fit(df[numeric_features + categorical_features])
    return preprocessor

# 3) 전체 데이터 변환 결과 캐싱
@st.cache_data
def transform_dataset(df, preprocessor, feature_cols):
    return preprocessor.transform(df[feature_cols])

def main():
    st.title('📊 학업 성취도 유사도 기반 조회')

    # --- 1) 데이터 및 파이프라인 준비 ---
    df = load_data()

    # 사용할 변수 목록
    numeric_features = [
        'age', 'study_hours_per_day', 'social_media_hours', 'netflix_hours',
        'attendance_percentage', 'sleep_hours', 'exercise_frequency',
        'internet_quality', 'mental_health_rating', 'previous_gpa',
        'semester', 'stress_level', 'social_activity', 'screen_time',
        'parental_support_level', 'motivation_level', 'exam_anxiety_score',
        'time_management_score'
    ]
    categorical_features = [
        'gender', 'major', 'part_time_job', 'diet_quality',
        'parental_education_level', 'extracurricular_participation',
        'dropout_risk', 'study_environment', 'access_to_tutoring',
        'family_income_range', 'learning_style'
    ]
    feature_cols = numeric_features + categorical_features

    preprocessor = create_preprocessor(df, numeric_features, categorical_features)
    X_all = transform_dataset(df, preprocessor, feature_cols)

    # 한국어 라벨 매핑
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
        'exercise_frequency': '운동 빈도(주당 횟수)',
        'parental_education_level': '부모 교육 수준',
        'internet_quality': '인터넷 품질',
        'mental_health_rating': '정신 건강 평가(1-10)',
        'extracurricular_participation': '과외 활동 참여',
        'previous_gpa': '이전 학기 GPA',
        'semester': '학기',
        'stress_level': '스트레스 수준',
        'dropout_risk': '퇴학 위험 여부',
        'social_activity': '사회 활동 수준',
        'screen_time': '화면 사용 시간(시간)',
        'study_environment': '학습 환경',
        'access_to_tutoring': '튜터링 접근성',
        'family_income_range': '가족 소득 범위',
        'parental_support_level': '부모 지원 수준',
        'motivation_level': '동기 수준',
        'exam_anxiety_score': '시험 불안 점수',
        'learning_style': '학습 스타일',
        'time_management_score': '시간 관리 점수'
    }

    st.sidebar.header('🎯 학생 특성 입력')
    user_input = {}

    # 4) 수치형 입력
    for feat in numeric_features:
        min_val = float(df[feat].min())
        max_val = float(df[feat].max())
        mean_val = float(df[feat].mean())

        if feat == 'semester':
            user_input[feat] = st.sidebar.number_input(
                labels[labels[feat]],
                min_value=int(min_val),
                max_value=int(max_val),
                value=int(round(mean_val))
            )
        else:
            user_input[feat] = st.sidebar.slider(
                labels[feat],
                min_value=min_val,
                max_value=max_val,
                value=mean_val
            )

    # 5) 범주형 입력
    for feat in categorical_features:
        options = df[feat].unique().tolist()
        user_input[feat] = st.sidebar.selectbox(
            labels[feat],
            options
        )

    # 6) 유사도 조회 버튼
    if st.sidebar.button('🔍 유사 학생 조회'):
        input_df = pd.DataFrame([user_input])
        X_input = preprocessor.transform(input_df[feature_cols])

        # 거리 계산 및 최소 거리 인덱스
        distances = np.linalg.norm(X_all - X_input, axis=1)
        idx = np.argmin(distances)
        similar = df.iloc[idx]

        st.subheader('👤 가장 유사한 학생 정보')
        # 관심 있는 컬럼만 표시 (원하면 더 추가)
        st.write({
            '이전 GPA': similar['previous_gpa'],
            '출석률(%)': similar['attendance_percentage'],
            '학기': int(similar['semester']),
            '스트레스 수준': similar['stress_level'],
            '시험 불안 점수': int(similar['exam_anxiety_score']),
            '최종 시험 점수': int(similar['exam_score'])
        })

        st.success(f"예상 시험 점수: **{int(similar['exam_score'])}점**")

if __name__ == '__main__':
    main()
