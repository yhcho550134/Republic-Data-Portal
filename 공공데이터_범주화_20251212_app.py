# import streamlit as st
# import pandas as pd

# # ---------------------------------------------------------
# # 1. 페이지 설정 (가장 먼저 실행)
# # ---------------------------------------------------------
# st.set_page_config(
#     page_title="공공데이터 비즈니스 포털",
#     page_icon="🏢",
#     layout="wide"  # 화면을 넓게 써서 시원한 느낌을 줍니다.
# )

# # ---------------------------------------------------------
# # 2. 스타일링 (CSS) - 글씨 크기 키우기 및 여백 조정
# # ---------------------------------------------------------
# st.markdown("""
#     <style>
#     .big-font {
#         font-size:20px !important;
#         font-weight: 500;
#     }
#     .stDataFrame {
#         font-size: 1.1rem; /* 테이블 글씨 크기 확대 */
#     }
#     /* 상단 헤더 여백 줄이기 */
#     .block-container {
#         padding-top: 2rem;
#         padding-bottom: 2rem;
#     }
#     </style>
#     """, unsafe_allow_html=True)

# # ---------------------------------------------------------
# # 3. 데이터 로드 (캐싱 적용으로 속도 향상)
# # ---------------------------------------------------------
# @st.cache_data
# def load_data():
#     file_path = '공공데이터_범주화_완료_v2.csv'
#     try:
#         df = pd.read_csv(file_path, encoding='utf-8-sig')
#     except:
#         df = pd.read_csv(file_path, encoding='cp949')
    
#     # URL 컬럼이 비어있으면 기본값 처리 (에러 방지)
#     df['상세URL'] = df['상세URL'].fillna('')
#     return df

# df = load_data()

# # ---------------------------------------------------------
# # 4. 사이드바 (검색 및 필터링 컨트롤 타워)
# # ---------------------------------------------------------
# with st.sidebar:
#     st.header("🔍 데이터 찾기")
#     st.write("원하는 조건으로 데이터를 검색하세요.")
    
#     # [A] 통합 검색 (키워드 입력)
#     search_query = st.text_input("검색어 입력 (제목, 키워드)", placeholder="예: 주차장, 전기차...")

#     st.divider()

#     # [B] 카테고리 필터 (가장 중요하므로 상단 배치)
#     # 전체 목록 + 카테고리 리스트
#     category_list = ["전체"] + sorted(list(df['Category'].unique()))
#     selected_category = st.selectbox("📂 비즈니스 주제 선택", category_list)

#     # [C] 지역 필터
#     # 지역 리스트 추출 (전체/기타 제외하고 가나다순)
#     region_options = sorted([r for r in df['Region'].dropna().unique() if r != "전국/기타"])
#     region_options = ["전체", "전국/기타"] + region_options
#     selected_region = st.selectbox("📍 지역 선택", region_options)

#     # [D] 상세 필터 (제공기관) - 너무 많으므로 Multiselect 활용
#     # 팁: 사용자가 먼저 주제를 고르면, 그 주제에 해당하는 기관만 보여주면 더 깔끔하겠지만,
#     # 여기서는 전체 기관 중 검색 가능하게 구현합니다.
#     st.divider()
#     with st.expander("🏢 제공기관별 상세 검색"):
#         all_providers = sorted(df['제공기관'].unique())
#         selected_providers = st.multiselect("기관명을 선택하거나 입력하세요", all_providers)

# # ---------------------------------------------------------
# # 5. 필터링 로직 (사용자 입력 반응)
# # ---------------------------------------------------------
# # 원본 데이터를 복사해서 필터링 진행
# filtered_df = df.copy()

# # 1. 카테고리 필터
# if selected_category != "전체":
#     filtered_df = filtered_df[filtered_df['Category'] == selected_category]

# # 2. 지역 필터
# if selected_region != "전체":
#     # 해당 지역 단어가 포함된 데이터 검색 (예: '서울' 선택 시 '서울,경기' 데이터도 포함되게 할지, 정확히 일치할지 결정)
#     # 여기서는 포함(contains) 로직 사용
#     filtered_df = filtered_df[filtered_df['Region'].str.contains(selected_region, na=False)]

# # 3. 제공기관 필터
# if selected_providers:
#     filtered_df = filtered_df[filtered_df['제공기관'].isin(selected_providers)]

# # 4. 텍스트 검색 (제목 + 키워드)
# if search_query:
#     # 대소문자 구분 없이 검색
#     mask = (
#         filtered_df['API명'].str.contains(search_query, case=False, na=False) | 
#         filtered_df['키워드'].str.contains(search_query, case=False, na=False)
#     )
#     filtered_df = filtered_df[mask]

# # ---------------------------------------------------------
# # 6. 메인 화면 구성
# # ---------------------------------------------------------
# st.title("🏢 공공데이터 비즈니스 인사이트 포털")
# st.markdown("비즈니스 기회 발굴을 위한 공공데이터 탐색 대시보드입니다.")

# # 상단 현황판 (Metrics)
# col1, col2, col3 = st.columns(3)
# with col1:
#     st.metric(label="총 데이터 수", value=f"{len(df):,} 건")
# with col2:
#     st.metric(label="검색된 데이터", value=f"{len(filtered_df):,} 건", delta=f"{len(filtered_df)-len(df):,} (필터링)")
# with col3:
#     if selected_category != "전체":
#         st.info(f"선택된 주제: **{selected_category}**")
#     else:
#         st.info("전체 주제 탐색 중")

# st.divider()

# # ---------------------------------------------------------
# # 7. 리스트 뷰 및 페이지네이션 UX
# # ---------------------------------------------------------

# # 보기 옵션 (한 줄에 배치)
# c1, c2 = st.columns([8, 2])
# with c1:
#     st.subheader(f"📋 검색 결과 리스트 ({len(filtered_df)}건)")
# with c2:
#     # 10건, 20건, ... 50건 선택
#     limit = st.selectbox("표시 개수", [10, 20, 30, 50, 100], index=1) # 기본 20건

# # 데이터가 없을 경우 처리
# if len(filtered_df) == 0:
#     st.warning("검색 조건에 맞는 데이터가 없습니다. 필터를 조정해주세요.")
# else:
#     # 데이터 슬라이싱 (상위 N개만 보여주기)
#     display_df = filtered_df.head(limit)

#     # 테이블에 보여줄 컬럼만 선택 및 정돈
#     display_columns = ['API명', 'Category', 'Region', '제공기관', '키워드', '상세URL']
    
#     # Streamlit의 강력한 기능: Dataframe Column Config
#     # URL을 클릭 가능한 링크로 바꿔주고, 카테고리에 색상을 입히는 등 설정
#     st.dataframe(
#         display_df[display_columns],
#         column_config={
#             "상세URL": st.column_config.LinkColumn(
#                 "바로가기", 
#                 help="클릭하면 공공데이터 포털 상세 페이지로 이동합니다.",
#                 display_text="🔗 이동"
#             ),
#             "Category": st.column_config.TextColumn(
#                 "비즈니스 주제",
#                 width="medium"
#             ),
#             "API명": st.column_config.TextColumn(
#                 "데이터 서비스명",
#                 width="large",
#                 help="API의 공식 명칭입니다."
#             ),
#             "키워드": st.column_config.TextColumn(
#                 "관련 태그",
#                 width="medium"
#             )
#         },
#         hide_index=True, # 인덱스 번호 숨김
#         use_container_width=True, # 화면 가로폭 꽉 채우기
#         height=int(35.2 * (limit + 1)) # 행 개수에 맞춰 높이 자동 조절 (대략적인 계산)
#     )

#     # 하단 안내
#     if len(filtered_df) > limit:
#         st.caption(f"ℹ️ 전체 {len(filtered_df)}개 중 상위 {limit}개만 표시됩니다. 더 세부적으로 검색해보세요.")

# # ---------------------------------------------------------
# # 8. 푸터
# # ---------------------------------------------------------
# st.markdown("---")
# st.markdown("Developed with 🐍 Python & Streamlit | Data Source: 공공데이터포털")


import streamlit as st
import pandas as pd
import math

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
# 4. 데이터 로드
# ---------------------------------------------------------
@st.cache_data
def load_data():
    file_path = '공공데이터_범주화_완료_v2.csv'
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except:
        df = pd.read_csv(file_path, encoding='cp949')
    df['상세URL'] = df['상세URL'].fillna('')
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
# 7. 메인 화면 구성
# ---------------------------------------------------------
st.title("🏢 공공데이터 비즈니스 인사이트 포털")
st.markdown("비즈니스 기회 발굴을 위한 공공데이터 탐색 대시보드입니다.")

# 현황판
# col1, col2, col3 = st.columns(3)
# with col1: st.metric("총 데이터 수", f"{len(df):,} 건")
# with col2: st.metric("검색된 데이터", f"{len(filtered_df):,} 건")
# with col3: 
#     if selected_category != "전체": st.info(f"선택된 주제: **{selected_category}**")
#     else: st.info("전체 주제 탐색 중")

# st.divider()
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

    # (4) 테이블 표시
    st.dataframe(
        display_df[['API명', 'Category', 'Region', '제공기관', '키워드', '상세URL']],
        column_config={
            "상세URL": st.column_config.LinkColumn("바로가기", display_text="🔗 이동", width="small"),
            "Category": st.column_config.TextColumn("비즈니스 주제", width="medium"),
            "API명": st.column_config.TextColumn("데이터 서비스명", width="large"),
            "키워드": st.column_config.TextColumn("관련 태그", width="large"), # 태그 잘 보이게 확장
            "Region": st.column_config.TextColumn("지역", width="small"),
            "제공기관": st.column_config.TextColumn("제공기관", width="medium"),
        },
        hide_index=True,
        use_container_width=True,
        height=(page_size + 1) * 35 + 3  # 행 개수에 맞춰 높이 자동 조절
    )

    # # (5) 하단 페이지네이션 버튼 (심플형)
    # st.markdown("---")
    # c1, col_prev, col_page, col_next, c5 = st.columns([5, 1, 2, 1, 5])

    # with col_prev:
    #     # 1페이지면 '이전' 버튼 비활성화
    #     if st.button("◀ 이전", disabled=(st.session_state.page == 1)):
    #         st.session_state.page -= 1
    #         st.rerun()

    # with col_page:
    #     # 현재 페이지 정보 표시 (가운데 정렬)
    #     st.markdown(
    #         f"<div style='text-align: center; padding-top: 5px; font-weight: bold;'>"
    #         f"{st.session_state.page} / {total_pages} 페이지"
    #         f"</div>", 
    #         unsafe_allow_html=True
    #     )

    # with col_next:
    #     # 마지막 페이지면 '다음' 버튼 비활성화
    #     if st.button("다음 ▶", disabled=(st.session_state.page == total_pages)):
    #         st.session_state.page += 1
    #         st.rerun()
# [여백] [이전] [페이지표시] [다음] [여백]
    # 양옆(10)을 아주 넓게 잡아서 가운데 요소들(0.8, 1.2, 0.8)을 중앙으로 밀집시킵니다.
    c1, c2, c3, c4, c5 = st.columns([10, 0.8, 1.2, 0.8, 10])

    with c2:
        if st.button("◀", use_container_width=True, disabled=(st.session_state.page == 1)):
            st.session_state.page -= 1
            st.rerun()

    with c3:
        # 텍스트 수직 정렬을 위한 스타일 (버튼 높이와 눈높이 맞춤)
        st.markdown(
            f"""
            <div style='
                text-align: center; 
                line-height: 42px; 
                font-weight: bold;
                font-size: 16px;
                white-space: nowrap;
            '>
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