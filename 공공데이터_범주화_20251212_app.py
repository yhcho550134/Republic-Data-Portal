import streamlit as st
import pandas as pd
import math
import json
import textwrap

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="공공데이터 비즈니스 포털",
    page_icon="🏢",
    layout="wide"
)

# ---------------------------------------------------------
# 2. 스타일링 (CSS)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: 500; }
    div[data-testid="stDataFrame"] { font-size: 1.05rem; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    
    /* 버튼 스타일 통일 */
    .stButton button { width: 100%; }
            
    /* [새로 추가] 대시보드 배지 스타일 */
    .dash-badge {
        display: inline-block;
        background-color: #E3F2FD;
        color: #1565C0;
        padding: 4px 10px;
        margin: 2px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 600;
        text-decoration: none;
        border: 1px solid #BBDEFB;
    }
    .dash-badge:hover {
        background-color: #2196F3;
        color: white;
    }
    /* 테이블 헤더 배경색 */
    th { background-color: #f8f9fa !important; }

            
    /* 사이드바 너비 늘리기 (350px로 설정, 더 넓게 하려면 숫자를 키우세요) */
    section[data-testid="stSidebar"] {
        min-width: 300px !important;
        max-width: 300px !important;
    }            
    </style>
    """, unsafe_allow_html=True)
    

# ---------------------------------------------------------
# 3. 세션 상태 초기화 (페이지 번호 기억하기)
# ---------------------------------------------------------
if 'page' not in st.session_state:
    st.session_state.page = 1

# 필터를 조작하면 페이지를 1로 초기화하는 함수
def reset_page():
    st.session_state.page = 1

# ---------------------------------------------------------
# 4. 데이터 로드 [수정됨: 대시보드 URL 컬럼 처리 추가]
# ---------------------------------------------------------
@st.cache_data
def load_data():
    file_path = '공공데이터_범주화_완료_v2.csv'
    
    # 1. 파일 읽기
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except:
        df = pd.read_csv(file_path, encoding='cp949')
    
    df['상세URL'] = df['상세URL'].fillna('')

    # 2. 대시보드 메타데이터(JSON) 로드
    try:
        with open('dashboard_meta.json', 'r', encoding='utf-8') as f:
            meta_list = json.load(f)
    except FileNotFoundError:
        # 파일이 없으면 빈 리스트로 처리 (에러 방지)
        meta_list = []

    # 3. API <-> 대시보드 연결 (HTML 태그 생성)
    dashboard_html_list = []
    dashboard_url_list = []

    # JSON에 있는 모든 대시보드 조건을 검사
    for idx, row in df.iterrows():
        target_text = str(row['API명']) + " " + str(row.get('키워드', '')) + " " + str(row.get('Category', ''))

        links = []
        raw_url = ''

        for dash in meta_list:
            if dash['related_api']:
                for keyword in dash['related_api']:
                    if keyword in target_text:
                        # 링크 생성 (target="_self"는 현재 탭, "_blank"는 새 탭)
                        # link_html = f"<a href='/{dash['url']}' target='_blank' class='dash-badge'>📊 {dash['name']}</a>"
                        link_html = f"<a href='{dash['url']}' target='_blank' class='dash-badge'>📊 {dash['name']}</a>"
                        links.append(link_html)
                        raw_url = dash['url']
                        break # 중복 방지 (한 대시보드는 한 번만)
        
        # 결과 저장
        # HTML 리스트 저장 (상단용)
        if not links:
            dashboard_html_list.append("<span style='color:#ccc; font-size:12px;'>-</span>")
        else:
            dashboard_html_list.append(" ".join(links)) # 여러 개면 옆으로 나열

        # URL 리스트 저장 (하단용)
        dashboard_url_list.append(raw_url)

    df['관련 대시보드'] = dashboard_html_list
    df['대시보드_URL'] = dashboard_url_list

    return df

df = load_data()

# ---------------------------------------------------------
# 5. 사이드바 (필터링) - 변경 시 reset_page 실행
# ---------------------------------------------------------
with st.sidebar:
    st.header("🔍 데이터 찾기")
    
    search_query = st.text_input("통합 검색", placeholder="예: 주차장, 전기차...", on_change=reset_page)
    st.divider()

    category_list = ["전체"] + sorted(list(df['Category'].unique()))
    selected_category = st.selectbox("📂 비즈니스 주제", category_list, on_change=reset_page)

    region_options = sorted([r for r in df['Region'].dropna().unique() if r != "전국/기타"])
    region_options = ["전체", "전국/기타"] + region_options
    selected_region = st.selectbox("📍 지역 선택", region_options, on_change=reset_page)

    st.divider()
    with st.expander("🏢 제공기관별 상세 검색"):
        all_providers = sorted(df['제공기관'].unique())
        selected_providers = st.multiselect("기관명을 선택하세요", all_providers, on_change=reset_page)

# ---------------------------------------------------------
# 6. 필터링 로직
# ---------------------------------------------------------
filtered_df = df.copy()

if selected_category != "전체":
    filtered_df = filtered_df[filtered_df['Category'] == selected_category]

if selected_region != "전체":
    filtered_df = filtered_df[filtered_df['Region'].str.contains(selected_region, na=False)]

if selected_providers:
    filtered_df = filtered_df[filtered_df['제공기관'].isin(selected_providers)]

if search_query:
    mask = (
        filtered_df['API명'].str.contains(search_query, case=False, na=False) | 
        filtered_df['키워드'].str.contains(search_query, case=False, na=False)
    )
    filtered_df = filtered_df[mask]

# ---------------------------------------------------------
# [추가] 6.5 정렬 로직 (대시보드 있는 데이터 상단 노출)
# ---------------------------------------------------------
# '대시보드_URL' 값 유무를 판단하여 내림차순 정렬 (True인 것이 위로 옴)
filtered_df['has_dashboard'] = filtered_df['대시보드_URL'].notna() & (filtered_df['대시보드_URL'] != '')
filtered_df = filtered_df.sort_values(by=['has_dashboard'], ascending=False)

# ---------------------------------------------------------
# 7. 메인 화면 구성
# ---------------------------------------------------------
st.title("🏢 공공데이터 비즈니스 인사이트 포털")
st.markdown("비즈니스 기회 발굴을 위한 공공데이터 탐색 대시보드입니다.")

# 상단 현황판 (Metrics)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="총 데이터 수", value=f"{len(df):,} 건")
with col2:
    st.metric(label="검색된 데이터", value=f"{len(filtered_df):,} 건", delta=f"{len(filtered_df)-len(df):,} (필터링)")
with col3:
    if selected_category != "전체":
        st.info(f"선택된 주제: **{selected_category}**")
    else:
        st.info("전체 주제 탐색 중")

st.divider()

# ---------------------------------------------------------
# 7.5 대시보드 확인 가능 API (상단 강조 영역) - [최종 정리]
# ---------------------------------------------------------

# 1. 데이터 필터링
# has_dashboard_mask = filtered_df['관련 대시보드'].astype(str).str.contains("<a ", case=False, na=False)
# featured_df = filtered_df[has_dashboard_mask].copy()

# if not featured_df.empty:
    
#     # 2. 보여줄 컬럼 정의
#     top_cols = ['관련 대시보드', 'API명', 'Category', 'Region', '제공기관', '관련태그', '상세URL']

#     # 3. 테이블 HTML 변환
#     table_html = featured_df[top_cols].to_html(
#         escape=False, 
#         index=False,
#         classes="featured-table", 
#         justify="left",
#         border=0
#     )

#     # 4. CSS와 HTML 조립 (줄바꿈 없이 한 줄로 처리하여 코드블록 인식 방지)
#     # f-string 안의 중괄호 {{ }}는 CSS 스타일용입니다.
#     raw_html = f"""
#     <style>
#         .dashboard-card {{
#             background-color: #ffffff;
#             border: 1px solid #E0E0E0;
#             border-radius: 10px;
#             padding: 24px;
#             box-shadow: 0 2px 8px rgba(0,0,0,0.05);
#             margin-bottom: 40px;
#         }}
#         .card-header-bar {{
#             border-left: 5px solid #1976D2;
#             padding-left: 12px;
#             margin-bottom: 15px;
#         }}
#         .featured-table {{
#             width: 100%;
#             border-collapse: collapse;
#         }}
#         .featured-table thead tr th {{
#             background-color: #F8F9FA !important;
#             color: #495057 !important;
#             font-weight: 600 !important;
#             border-bottom: 2px solid #dee2e6 !important;
#             font-size: 14px !important;
#             text-align: left !important;
#         }}
#         .featured-table tbody tr td {{
#             padding: 12px 10px !important;
#             vertical-align: middle !important;
#             border-bottom: 1px solid #eee !important;
#             font-size: 14px !important;
#         }}
#     </style>

#     <div class="dashboard-card">
#         <div class="card-header-bar">
#             <h4 style="margin:0; color:#333; font-weight:700; font-size:1.1rem;">
#                 📊 대시보드 확인 가능 API
#             </h4>
#         </div>
#         <p style="margin:0 0 20px 0; font-size:14px; color:#666;">
#             아래 리스트는 데이터 시각화가 완료된 API입니다. 
#             <span style="background-color:#E3F2FD; color:#1565C0; padding:2px 8px; border-radius:4px; font-weight:600; font-size:12px;">분석 배지 버튼</span>을 클릭하면 대시보드 화면으로 이동합니다.
#         </p>
#         <div style="overflow-x:auto;">
#             {table_html}
#         </div>
#     </div>
#     """

#     # 5. [핵심] 줄바꿈을 모두 제거하여 한 줄로 만듦 (그래야 HTML로 제대로 인식됨)
#     clean_html = raw_html.replace("\n", "").strip()

#     # 6. 화면 출력
#     st.markdown(clean_html, unsafe_allow_html=True)

has_dashboard_mask = filtered_df['관련 대시보드'].astype(str).str.contains("<a ", case=False, na=False)
featured_df = filtered_df[has_dashboard_mask].copy()

if not featured_df.empty:
    # -----------------------------------------------------
    # [수정됨] 컬럼 이름 변경 및 링크 디자인 적용 로직
    # -----------------------------------------------------

    # 1. '상세URL'을 '🔗 이동' 하이퍼링크로 변환
    featured_df['상세URL'] = featured_df['상세URL'].apply(
        lambda x: f"<a href='{x}' target='_blank' style='text-decoration:none; color:#1976D2; font-weight:bold;'>🔗 이동</a>" if x else ""
    )

    # 2. 컬럼 이름 변경 (영어 -> 한글)
    rename_map = {
        '관련 대시보드': '📊 분석 대시보드',
        'API명': '데이터 서비스명',
        'Category': '비즈니스 주제',
        'Region': '지역',
        '제공기관': '제공기관',
        '키워드': '관련 태그',
        '상세URL': '원본 링크'
    }
    
    # 3. 화면에 보여줄 순서대로 컬럼 선택 및 이름 변경
    display_cols = ['관련 대시보드', 'API명', 'Category', 'Region', '제공기관', '키워드', '상세URL']
    display_df = featured_df[display_cols].rename(columns=rename_map)

    # 4. 테이블 HTML 변환
    table_html = display_df.to_html(
        escape=False, 
        index=False,
        classes="featured-table", 
        justify="left",
        border=0
    )

    # 5. 디자인 및 출력 (줄바꿈 제거 방식 유지)
    raw_html = f"""
    <style>
        .dashboard-card {{
            background-color: #ffffff;
            border: 1px solid #E0E0E0;
            border-radius: 10px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 40px;
        }}
        .card-header-bar {{
            border-left: 5px solid #1976D2;
            padding-left: 12px;
            margin-bottom: 15px;
        }}
        .featured-table {{
            width: 100%;
            border-collapse: collapse;
            white-space: nowrap;
        }}
        .featured-table thead tr th {{
            background-color: #F8F9FA !important;
            color: #495057 !important;
            font-weight: 600 !important;
            border-bottom: 2px solid #dee2e6 !important;
            font-size: 14px !important;
            text-align: left !important;
            padding: 12px 10px !important;
        }}
        .featured-table tbody tr td {{
            padding: 12px 10px !important;
            vertical-align: middle !important;
            border-bottom: 1px solid #eee !important;
            font-size: 14px !important;
            color: #333 !important;
        }}
    </style>

    <div class="dashboard-card">
        <div class="card-header-bar">
            <h4 style="margin:0; color:#333; font-weight:700; font-size:1.1rem;">
                📊 대시보드 확인 가능 API
            </h4>
        </div>
        <p style="margin:0 0 20px 0; font-size:14px; color:#666;">
            아래 리스트는 데이터 시각화가 완료된 API입니다. 
            <span style="background-color:#E3F2FD; color:#1565C0; padding:2px 8px; border-radius:4px; font-weight:600; font-size:12px;">분석 배지 버튼</span>을 클릭하면 대시보드 화면으로 이동합니다.
        </p>
        <div style="overflow-x:auto;">
            {table_html}
        </div>
    </div>
    """

    st.markdown(raw_html.replace("\n", "").strip(), unsafe_allow_html=True)
# ---------------------------------------------------------
# 8. 리스트 뷰 및 페이지네이션
# ---------------------------------------------------------

# (1) 보기 옵션 설정
c1, c2 = st.columns([8, 2])
with c1:
    st.subheader(f"📋 검색 결과 리스트")
with c2:
    page_size = st.selectbox("표시 개수", [10, 20, 30, 50], index=1, on_change=reset_page)

# (2) 페이지 계산
total_items = len(filtered_df)
total_pages = math.ceil(total_items / page_size)

# 데이터가 없을 경우 처리
if total_items == 0:
    st.warning("검색 조건에 맞는 데이터가 없습니다.")
else:
    # 페이지 범위 안전장치
    if st.session_state.page > total_pages: st.session_state.page = total_pages
    if st.session_state.page < 1: st.session_state.page = 1
    
    # (3) 데이터 자르기 (Slicing)
    start_idx = (st.session_state.page - 1) * page_size
    end_idx = start_idx + page_size
    display_df = filtered_df.iloc[start_idx:end_idx]

    # (4) 테이블 표시 [수정됨: 컬럼 설정 추가]
    st.dataframe(
        # 화면에 보여줄 컬럼 순서 지정 (대시보드_URL을 맨 앞에 배치)
        display_df[['API명', 'Category', 'Region', '제공기관', '키워드', '상세URL', '대시보드_URL']],
        column_config={
            # [핵심] 대시보드 링크 버튼 설정
            "대시보드_URL": st.column_config.LinkColumn(
                "📊 분석 대시보드",      # 헤더 이름
                display_text="분석 보기", # 값이 있을 때 보여줄 텍스트
                help="클릭하면 상세 분석 페이지로 이동합니다.",
                width="small"
            ),
            "상세URL": st.column_config.LinkColumn("원본 링크", display_text="🔗 이동", width="small"),
            "Category": st.column_config.TextColumn("비즈니스 주제", width="medium"),
            "API명": st.column_config.TextColumn("데이터 서비스명", width="large"),
            "키워드": st.column_config.TextColumn("관련 태그", width="large"),
            "Region": st.column_config.TextColumn("지역", width="small"),
            "제공기관": st.column_config.TextColumn("제공기관", width="medium"),
        },
        hide_index=True,
        use_container_width=True,
        height=(page_size + 1) * 35 + 3
    )

    # 페이지네이션 컨트롤
    c1, c2, c3, c4, c5 = st.columns([10, 0.8, 1.2, 0.8, 10])

    with c2:
        if st.button("◀", use_container_width=True, disabled=(st.session_state.page == 1)):
            st.session_state.page -= 1
            st.rerun()

    with c3:
        st.markdown(
            f"""
            <div style='text-align: center; line-height: 42px; font-weight: bold; font-size: 16px; white-space: nowrap;'>
                {st.session_state.page} / {total_pages}
            </div>
            """, 
            unsafe_allow_html=True
        )

    with c4:
        if st.button("▶", use_container_width=True, disabled=(st.session_state.page == total_pages)):
            st.session_state.page += 1
            st.rerun()

# ---------------------------------------------------------
# 9. 푸터
# ---------------------------------------------------------
st.markdown("---")
st.markdown("Developed with 🐍 Python & Streamlit")

