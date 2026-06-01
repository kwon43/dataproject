import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# 페이지 설정
st.set_page_config(page_title="기온 상승 트렌드 분석", layout="wide")

st.title("🌡️ 1980년대 전후 기온 상승 경향 비교 분석")
st.markdown("""
1980년대 이전과 이후의 기온 상승 속도와 양상에 차이가 있을 것이라는 가설을 검증하기 위한 웹앱입니다.
업로드된 서울 기온 데이터를 바탕으로 회귀 분석 선과 분포 차이를 확인해 보세요.
""")

# 데이터 로드 함수 (캐싱 적용)
@st.cache_data
def load_data():
    # 데이터 읽기 (전체 경로 대신 파일명만 사용하도록 유연하게 설정)
    try:
        df = pd.read_csv("ta_20260601093156.csv")
    except FileNotFoundError:
        st.error("⚠️ 데이터 파일(`ta_20260601093156.csv`)을 찾을 수 없습니다. 앱과 같은 폴더에 넣어주세요.")
        return None
    
    # 컬럼명 공백 제거 및 날짜 데이터 정제
    df.columns = df.columns.str.strip()
    df['날짜'] = df['날짜'].astype(str).str.replace(r'[\t\s"]', '', regex=True)
    df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
    df = df.dropna(subset=['날짜'])
    
    # 연도 컬럼 생성
    df['연도'] = df['날짜'].dt.year
    return df

df = load_data()

if df is not None:
    # 1. 데이터 필터링 및 연도별 평균 계산
    annual_df = df.groupby('연도')[['평균기온(℃)', '최저기온(℃)', '최고기온(℃)']].mean().reset_index()
    
    # 1980년 기준으로 데이터 분할 (1980년 포함 여부 선택 가능)
    annual_df['기간'] = np.where(annual_df['연도'] < 1980, '1980년 이전', '1980년 이후')
    
    # 대시보드 레이아웃 (주요 지표 표시)
    col1, col2, col3 = st.columns(3)
    
    mean_before = annual_df[annual_df['기간'] == '1980년 이전']['평균기온(℃)'].mean()
    mean_after = annual_df[annual_df['기간'] == '1980년 이후']['평균기온(℃)'].mean()
    
    with col1:
        st.metric(label="1980년 이전 평균 기온", value=f"{mean_before:.2f} ℃")
    with col2:
        st.metric(label="1980년 이후 평균 기온", value=f"{mean_after:.2f} ℃", delta=f"{mean_after - mean_before:+.2f} ℃")
    with col3:
        st.metric(label="전체 데이터 연도 범위", value=f"{annual_df['연도'].min()}년 ~ {annual_df['연도'].max()}년")
        
    st.markdown("---")
    
    # 사이드바 제어 요소
    st.sidebar.header("📊 시각화 설정")
    temp_type = st.sidebar.selectbox("분석할 기온 유형 선택", ['평균기온(℃)', '최저기온(℃)', '최고기온(℃)'])
    
    # 2. 메인 시각화: 회귀 분석 추세선 비교
    st.subheader(f"📈 {temp_type} 연도별 변화 및 추세선 비교")
    
    fig = px.scatter(annual_df, x='연도', y=temp_type, color='기간', 
                     color_discrete_map={'1980년 이전': '#3498db', '1980년 이후': '#e74c3c'},
                     trendline="ols", trendline_scope="trace",
                     title=f"1980년 전후 {temp_type} 상승 기울기 변화 (OLS 회귀선 포함)")
    
    fig.update_layout(xaxis_title="연도", yaxis_title=f"{temp_type}", legend_title="구분")
    st.plotly_chart(fig, use_container_width=True)
    
    # 통계적 수치 계산 (기울기 비교)
    st.markdown("### 🔍 가설 검증 결과 요약")
    
    # 1980 이전/이후 기울기 추출
    results = px.get_trendline_results(fig)
    
    try:
        slope_before = results.iloc[0]["px_fit_results"].params[1]
        slope_after = results.iloc[1]["px_fit_results"].params[1]
        
        st.write(f"👉 **1980년 이전** 1년당 기온 상승 폭: **{slope_before:.4f} ℃**")
        st.write(f"👉 **1980년 이후** 1년당 기온 상승 폭: **{slope_after:.4f} ℃**")
        
        if slope_after > slope_before:
            st.success(f"💡 **가설 지지!** 1980년 이후 기온 상승 속도가 이전보다 약 **{slope_after/slope_before:.1f}배** 더 빨라졌습니다.")
        else:
            st.info("💡 1980년 이전의 상승 속도가 더 가파르거나 큰 차이가 없습니다.")
    except:
        st.write("※ 추세선 데이터를 계산하는 중입니다.")
        
    st.markdown("---")
    
    # 3. 분포 비교 (Box Plot)
    st.subheader("📊 기온 데이터 분포 차이 확인")
    fig_box = px.box(annual_df, x='기간', y=temp_type, color='기간',
                     color_discrete_map={'1980년 이전': '#3498db', '1980년 이후': '#e74c3c'},
                     points="all", title=f"1980년 전후 {temp_type} 분포 비교")
    st.plotly_chart(fig_box, use_container_width=True)
