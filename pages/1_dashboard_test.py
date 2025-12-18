# 파일 위치: pages/dashboard_test.py
import streamlit as st
import pandas as pd
import numpy as np

# 대시보드 제목
st.title("📊 상세 대시보드 예시")
st.success("축하합니다! 메인 페이지에서 링크를 타고 성공적으로 이동했습니다.")

# 가짜 데이터로 차트 그리기 (Dash 대신 Streamlit 차트 예시)
st.subheader("데이터 시각화 영역")
chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['A', 'B', 'C']
)
st.bar_chart(chart_data)

st.info("여기에 나중에 Dash에서 변환한 코드를 넣으면 됩니다.")
