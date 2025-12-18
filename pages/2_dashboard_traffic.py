import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. 데이터 로딩 및 전처리 (Dash 코드의 로직을 그대로 가져옴)
# -----------------------------------------------------------------------------
# @st.cache_data는 데이터를 매번 새로 읽지 않고 메모리에 저장해두는 기능입니다. (속도 향상)
@st.cache_data
def load_data():
    def read_any(path):
        """한글 CSV 깨짐 방지를 위한 함수"""
        for enc in ["utf-8-sig", "cp949", "euc-kr"]:
            try:
                return pd.read_csv(path, encoding=enc)
            except Exception:
                continue
        return pd.read_csv(path)

    # 1) 버스 데이터 로딩
    # (주의: CSV 파일이 main.py와 같은 폴더에 있어야 합니다)
    try:
        bus_raw = read_any("서울_9월_버스이용_구포함_최종완성.csv")
        bus_df = bus_raw.copy()
        bus_df["date"] = pd.to_datetime(bus_df["사용일자"].astype(str), format="%Y%m%d", errors="coerce")
        bus_df["board"] = pd.to_numeric(bus_df["승차총승객수"], errors="coerce").fillna(0).astype(int)
        bus_df["alight"] = pd.to_numeric(bus_df["하차총승객수"], errors="coerce").fillna(0).astype(int)
        bus_df["total"] = bus_df["board"] + bus_df["alight"]
        bus_df["line"] = bus_df["노선명"].astype(str)
        bus_df["station"] = bus_df["역명"].astype(str)
        bus_df["mode"] = "버스"
        bus_df["bus_region"] = bus_df["버스_자치구"].astype(str) if "버스_자치구" in bus_df.columns else None
        bus_df["sub_line"] = None
    except FileNotFoundError:
        st.error("⚠️ '서울_9월_버스이용_구포함_최종완성.csv' 파일이 없습니다.")
        return pd.DataFrame() # 빈 데이터프레임 반환

    # 2) 지하철 데이터 로딩
    try:
        subway_raw = read_any("서울_9월_지하철이용.csv")
        # 인덱스 밀림 현상 처리 (Dash 코드와 동일)
        sub_reset = subway_raw.reset_index()
        sub_df = sub_reset.rename(
            columns={
                "index": "사용일자", "사용일자": "노선명", "노선명": "역명",
                "역명": "승차총승객수", "승차총승객수": "하차총승객수", "하차총승객수": "등록일자"
            }
        )
        sub_df["date"] = pd.to_datetime(sub_df["사용일자"].astype(str), format="%Y%m%d", errors="coerce")
        sub_df["board"] = pd.to_numeric(sub_df["승차총승객수"], errors="coerce").fillna(0).astype(int)
        sub_df["alight"] = pd.to_numeric(sub_df["하차총승객수"], errors="coerce").fillna(0).astype(int)
        sub_df["total"] = sub_df["board"] + sub_df["alight"]
        sub_df["line"] = sub_df["노선명"].astype(str)
        sub_df["station"] = sub_df["역명"].astype(str)
        sub_df["mode"] = "지하철"
        sub_df["bus_region"] = None
        sub_df["sub_line"] = sub_df["line"]
    except FileNotFoundError:
        st.error("⚠️ '서울_9월_지하철이용.csv' 파일이 없습니다.")
        return pd.DataFrame()

    # 3) 통합
    use_cols = ["date", "mode", "line", "station", "board", "alight", "total", "bus_region", "sub_line"]
    all_df = pd.concat([bus_df[use_cols], sub_df[use_cols]], ignore_index=True)
    
    return all_df

# 데이터 불러오기
df = load_data()

# -----------------------------------------------------------------------------
# 2. 화면 레이아웃 구성 (UI)
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="대중교통 분석")

st.title("📊 서울 대중교통 유동인구 대시보드")
st.markdown("""
<div style="background-color:#f0f2f6; padding:10px; border-radius:5px; margin-bottom:20px;">
    9월 한 달간 버스·지하철 승·하차 데이터를 기반으로 <b>광고 입지</b>를 탐색합니다.
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.stop() # 데이터가 없으면 여기서 멈춤

# --- 필터 영역 (상단) ---
with st.expander("🔎 필터 옵션 열기/닫기", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 날짜 범위 선택
        min_date = df["date"].min().date()
        max_date = df["date"].max().date()
        date_range = st.date_input(
            "📅 기간 선택",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    
    with col2:
        # 교통수단 선택
        mode_option = st.radio("🚉 교통수단", ["전체(버스+지하철)", "버스만", "지하철만"], horizontal=True)
        # 로직 처리를 위해 변수 변환
        if "버스만" in mode_option: selected_mode = "bus"
        elif "지하철만" in mode_option: selected_mode = "subway"
        else: selected_mode = "all"

    with col3:
        # 지표 선택
        metric_option = st.radio("📊 분석 지표", ["유동인구(합계)", "승차", "하차"], horizontal=True)
        metric_map = {"유동인구(합계)": "total", "승차": "board", "하차": "alight"}
        selected_metric = metric_map[metric_option]

    # 하단 상세 필터 (버스 구 / 지하철 호선)
    col4, col5 = st.columns(2)
    with col4:
        # 버스 자치구 목록 추출
        bus_regions = sorted(df[df["mode"]=="버스"]["bus_region"].dropna().unique())
        selected_region = st.selectbox("🚌 버스 자치구", ["전체"] + list(bus_regions))
    
    with col5:
        # 지하철 호선 목록 추출
        sub_lines = sorted(df[df["mode"]=="지하철"]["sub_line"].dropna().unique())
        selected_line = st.selectbox("🚇 지하철 호선", ["전체"] + list(sub_lines))

# -----------------------------------------------------------------------------
# 3. 데이터 필터링 로직
# -----------------------------------------------------------------------------
# 1) 날짜 필터
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    mask_date = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
    filtered_df = df.loc[mask_date].copy()
else:
    filtered_df = df.copy()

# 2) 모드 필터
if selected_mode == "bus":
    filtered_df = filtered_df[filtered_df["mode"] == "버스"]
elif selected_mode == "subway":
    filtered_df = filtered_df[filtered_df["mode"] == "지하철"]

# 3) 상세 필터 (버스 구 / 지하철 호선)
if selected_mode in ["all", "bus"] and selected_region != "전체":
    # 버스이면서 해당 구가 아닌 데이터 제외 (주의: 모드가 'all'일 때는 지하철 데이터는 살려둬야 함)
    # 하지만 Dash 로직을 따라가면, 상세 필터를 걸면 해당 데이터만 보는 것이 일반적임
    # 여기서는 직관적으로: 선택한 구의 버스 데이터만 남김 (all 모드일 경우 지하철은 그대로 둠? -> 보통은 필터링된 것만 봄)
    # Dash 코드 로직: (mode != '버스') | (bus_region == region) -> 버스가 아니거나, 버스라면 그 지역인 것
    filtered_df = filtered_df[(filtered_df["mode"] != "버스") | (filtered_df["bus_region"] == selected_region)]

if selected_mode in ["all", "subway"] and selected_line != "전체":
    filtered_df = filtered_df[(filtered_df["mode"] != "지하철") | (filtered_df["sub_line"] == selected_line)]


# -----------------------------------------------------------------------------
# 4. KPI 카드 (st.metric 사용)
# -----------------------------------------------------------------------------
st.markdown("---")
kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

bus_sum = filtered_df.loc[filtered_df["mode"] == "버스", "total"].sum()
sub_sum = filtered_df.loc[filtered_df["mode"] == "지하철", "total"].sum()
total_sum = bus_sum + sub_sum
bus_count = filtered_df.loc[filtered_df["mode"] == "버스", "station"].nunique()
sub_count = filtered_df.loc[filtered_df["mode"] == "지하철", "station"].nunique()

kpi_col1.metric("🚌 버스 유동인구", f"{bus_sum:,.0f}명")
kpi_col2.metric("🚇 지하철 유동인구", f"{sub_sum:,.0f}명")
kpi_col3.metric("👥 총 유동인구", f"{total_sum:,.0f}명")
kpi_col4.metric("🚏 버스 정류장 수", f"{bus_count:,.0f}개")
kpi_col5.metric("🚉 지하철 역 수", f"{sub_count:,.0f}개")

# -----------------------------------------------------------------------------
# 5. 그래프 영역
# -----------------------------------------------------------------------------
st.markdown("### 📈 데이터 시각화")
chart_col1, chart_col2 = st.columns([7, 5])

# [왼쪽] 트렌드 그래프
with chart_col1:
    st.subheader("일자별/유형별 추이")
    
    if filtered_df.empty:
        st.info("데이터가 없습니다.")
    else:
        # Dash 코드의 로직 구현
        if selected_mode == "all":
            # 일자별 라인 차트
            g = filtered_df.groupby(["date", "mode"])[selected_metric].sum().reset_index()
            fig_trend = px.line(g, x="date", y=selected_metric, color="mode", markers=True, 
                                title="일자별 유동인구 (버스 vs 지하철)")
        elif selected_mode == "bus":
            # 자치구별 막대 차트
            g = filtered_df[filtered_df["mode"]=="버스"].groupby("bus_region")[selected_metric].sum().reset_index()
            fig_trend = px.bar(g, x="bus_region", y=selected_metric, title="자치구별 버스 유동인구",
                               labels={"bus_region": "자치구"})
        elif selected_mode == "subway":
            # 호선별 막대 차트
            g = filtered_df[filtered_df["mode"]=="지하철"].groupby("sub_line")[selected_metric].sum().reset_index()
            fig_trend = px.bar(g, x="sub_line", y=selected_metric, title="호선별 지하철 유동인구",
                               labels={"sub_line": "호선"})
            
        st.plotly_chart(fig_trend, use_container_width=True)

# [오른쪽] TOP N 랭킹
with chart_col2:
    st.subheader("🏆 상위 정류장/역 TOP N")
    top_n = st.slider("상위 개수 선택", 5, 50, 10, 5)
    
    if filtered_df.empty:
        st.info("데이터가 없습니다.")
    else:
        if selected_mode == "all":
            g_top = filtered_df.groupby("station")[selected_metric].sum().reset_index()
            color_opt = None
        else:
            g_top = filtered_df.groupby(["station", "mode"])[selected_metric].sum().reset_index()
            color_opt = "mode"
            
        g_top = g_top.sort_values(selected_metric, ascending=False).head(top_n)
        
        fig_top = px.bar(g_top, x=selected_metric, y="station", color=color_opt, orientation="h",
                         title=f"상위 {top_n}개 정류장/역")
        fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top, use_container_width=True)

# -----------------------------------------------------------------------------
# 6. 상세 테이블
# -----------------------------------------------------------------------------
st.markdown("### 📋 상세 데이터 조회")
with st.expander("데이터 테이블 보기", expanded=True):
    search_text = st.text_input("🔍 정류장/역 이름 검색", placeholder="예: 강남, 홍대입구...")
    
    # 테이블용 집계
    table_df = filtered_df.groupby(["station", "mode", "bus_region", "sub_line"], dropna=False)[
            ["board", "alight", "total"]
        ].sum().reset_index()
    
    # 검색 필터
    if search_text:
        table_df = table_df[table_df["station"].str.contains(search_text)]
    
    # 정렬 및 컬럼 정리
    table_df = table_df.sort_values("total", ascending=False)
    table_df = table_df.rename(columns={"bus_region": "구", "sub_line": "호선", "mode": "교통수단",
                                        "board": "승차", "alight": "하차", "total": "합계"})
    
    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "합계": st.column_config.NumberColumn(format="%d명"),
            "승차": st.column_config.NumberColumn(format="%d명"),
            "하차": st.column_config.NumberColumn(format="%d명"),
        }
    )
