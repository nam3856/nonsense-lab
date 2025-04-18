import os
import streamlit as st
import random
import time
import uuid
from dotenv import load_dotenv
from openai import OpenAI
from backend.backend_utils import search_papers_by_keywords
from backend.openai_fakegen import generate_fake_paper
from backend.vector_store import PaperVectorStore

# Load environment variables
load_dotenv()
DBPIA_API_KEY = os.getenv("DBPIA_API_KEY")

# Page configuration
st.set_page_config(
    page_title="FakePaperia",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 세션 상태 초기화
if 'search_id' not in st.session_state:
    st.session_state.search_id = None
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None
if 'current_query' not in st.session_state:
    st.session_state.current_query = None

# 오래된 벡터 저장소 정리
vector_store = PaperVectorStore()
vector_store.cleanup_old_stores(max_age_hours=24)  # 24시간 이상 된 저장소 삭제

# Fun loading messages
LOADING_MESSAGES = [
    "🤔 교수님께 낼 논문을 열심히 만들고 있습니다...",
    "🎲 랜덤 참고문헌 생성중...",
    "📚 없는 연구 결과를 만들어내는 중...",
    "🎭 진짜같은 가짜 데이터를 조작하는 중...",
    "🎨 그럴듯한 그래프를 그리는 중...",
    "✍️ 현란한 학술 용어를 뽑아내는 중...",
    "🎯 p-value 조작하는 중...",
    "🎪 논문 심사위원을 현혹시키는 중...",
    "🎭 가짜 연구진을 만드는 중...",
    "🎪 학회 이름을 지어내는 중..."
]

# Fun paper styles
PAPER_STYLES = [
    "📜 황당무계 학회지",
    "🎭 허구연구 저널",
    "🎪 망상과학 논문집",
    "🎨 상상력 연구회보",
    "🎯 헛소리 학술지"
]

# Custom CSS for yellow theme styling
st.markdown("""
<style>
    /* Reset default padding */
    .block-container {
        padding-top: 0 !important;
    }
    
    /* Top navigation bar */
    .top-nav {
        background-color: white;
        padding: 1rem 2rem;
        border-bottom: 1px solid #FFD700;
    }
    
    /* Logo and search container */
    .logo-search-container {
        display: flex;
        align-items: center;
        gap: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Search container styling */
    div.stSelectbox > div > div {
        border: 2px solid #FFD700 !important;
        border-right: none !important;
        border-radius: 4px 0 0 4px !important;
    }
    
    /* Remove focus outline from selectbox */
    div.stSelectbox > div:focus-within {
        box-shadow: 0 0 0 2px rgba(0,0,0,0.1) !important;
    }
    
    /* Text input styling */
    div.stTextInput > div > div > input {
        border: 2px solid #FFD700 !important;
    }
    
    /* Remove red focus outline from text input */
    div.stTextInput > div:focus-within {
        box-shadow: 0 0 0 2px rgba(0,0,0,0.1) !important;
    }
    
    /* Button styling */
    div.stButton > button {
        border: 2px solid #FFD700 !important;
        background-color: #FFD700 !important;
        color: black !important;
        padding: 0 2rem !important;
    }
    
    div.stButton > button:hover {
        border-color: #FFE55C !important;
        background-color: #FFE55C !important;
    }
    
    div.stButton > button:active {
        background-color: #FFD700 !important;
        border-color: #FFD700 !important;
    }
    
    /* Generated paper styling */
    .paper-container {
        background-color: white;
        padding: 2rem;
        margin: 2rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(255, 215, 0, 0.2);
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Fun paper header */
    .paper-header {
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background-color: #FFF8DC;
        border-radius: 8px;
    }
    
    .paper-journal {
        font-size: 1.2rem;
        color: #B8860B;
        margin-bottom: 0.5rem;
    }
    
    .paper-date {
        font-size: 0.9rem;
        color: #666;
    }
    
    /* Loading animation */
    .loading-container {
        text-align: center;
        padding: 2rem;
        background-color: #FFF8DC;
        border-radius: 8px;
        margin: 2rem;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: white;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre;
        font-size: 1rem;
        color: #666;
        border-radius: 4px 4px 0 0;
    }
    
    /* Override tab focus and selection colors */
    .stTabs [data-baseweb="tab"]:focus {
        color: black !important;
        box-shadow: none !important;
        outline: none !important;
        border: none !important;
        background: none !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: transparent !important;
        color: black !important;
        border-bottom: 2px solid #FFD700 !important;
    }
    
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    
    /* Remove all Streamlit focus indicators */
    :focus {
        outline: none !important;
    }
    
    /* Style for select dropdown */
    div[data-baseweb="select"] > div {
        cursor: pointer !important;
    }
    
    /* Enable pointer events for all interactive elements */
    .stSelectbox, .stTextInput, .stButton {
        pointer-events: auto !important;
        z-index: 1000 !important;
    }
    
    button, select, input {
        pointer-events: auto !important;
        z-index: 1000 !important;
    }
    
    /* Fix clickable elements */
    .stButton > button, 
    .stSelectbox > div, 
    .stTextInput > div {
        position: relative !important;
        z-index: 1000 !important;
        pointer-events: auto !important;
    }
    
    /* Ensure elements are clickable */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    div[data-baseweb="button"] > button {
        position: relative !important;
        z-index: 1000 !important;
        pointer-events: auto !important;
    }
</style>
""", unsafe_allow_html=True)

# Top Navigation Bar with Logo and Search
st.markdown('<div class="top-nav">', unsafe_allow_html=True)
st.markdown('<div class="logo-search-container">', unsafe_allow_html=True)

# Logo column
col1, col2, col3, col4 = st.columns([2, 2, 6, 2])

with col1:
    st.image("개열받는로고.png", width=150)

with col2:
    search_type = st.selectbox(
        "검색 유형",
        ["진짜같은 가짜 논문", "일반 논문"],
        label_visibility="collapsed",
        key="search_type"
    )

with col3:
    search_query = st.text_input(
        "검색어를 입력하세요",
        placeholder="어떤 논문을 찾고 계신가요?",
        label_visibility="collapsed",
        key="search_query"
    )

with col4:
    search_button = st.button(
        "검색",
        use_container_width=True,
        key="search_button"
    )

st.markdown('</div></div>', unsafe_allow_html=True)

# Category Tabs
tabs = st.tabs(["AI 검색", "오늘의 괴논문", "최근 검색 키워드"])

with tabs[0]:
    # Paper Generation
    if search_button and search_query:
        if search_type == "진짜같은 가짜 논문":
            # 새로운 검색어이거나 벡터 저장소가 없는 경우에만 논문 검색
            if st.session_state.current_query != search_query or st.session_state.vector_store is None:
                # Fun loading animation with random messages
                loading_placeholder = st.empty()
                with loading_placeholder:
                    st.markdown(f"""
                    <div class="loading-container">
                        <h3>🔍 관련 논문을 검색하고 있습니다...</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 논문 검색
                    result = search_papers_by_keywords(search_query, DBPIA_API_KEY)
                    
                    if result['papers']:
                        # 새로운 검색 ID 생성
                        search_id = str(uuid.uuid4())
                        st.session_state.search_id = search_id
                        
                        # 벡터 저장소 경로 설정
                        vector_store_path = f"vectorstore/paper_vectors_{search_id}"
                        
                        # 벡터 저장소 생성
                        vector_store = PaperVectorStore()
                        vector_store.add_papers(result['papers'])
                        vector_store.save(vector_store_path)
                        
                        # 세션 상태 업데이트
                        st.session_state.vector_store = vector_store
                        st.session_state.current_query = search_query
                        
                        # 키워드 표시
                        st.success(f"✅ 총 {len(result['papers'])}개의 관련 논문을 찾았습니다!")
                        st.markdown(f"**추출된 키워드:** {', '.join(result['keywords'])}")
                    else:
                        st.error("❌ 관련 논문을 찾지 못했습니다.")
                        loading_placeholder.empty()
                        st.stop()
            
            # 논문 생성
            loading_placeholder = st.empty()
            for i in range(3):  # Show 3 different loading messages
                with loading_placeholder:
                    st.markdown(f"""
                    <div class="loading-container">
                        <h3>{random.choice(LOADING_MESSAGES)}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(1)
            
            # Generate paper using backend
            fake_paper = generate_fake_paper(
                vector_store=st.session_state.vector_store,
                query=search_query,
                max_tokens=2048
            )
            
            # Clear loading animation
            loading_placeholder.empty()
            
            # Add fun paper header
            journal_style = random.choice(PAPER_STYLES)
            current_date = time.strftime("%Y년 %m월 %d일")
            
            # Display paper with sections
            references_html = []
            for ref in fake_paper['references'].split('\n'):
                if ref.strip():
                    references_html.append(f'<div style="margin-bottom: 0.8em; margin-left: 2em; text-indent: -2em; line-height: 1.6; font-size: 0.95em;">{ref}</div>')
            references_html = '\n'.join(references_html)

            st.markdown(f"""
            <div class="paper-container">
                <div class="paper-header">
                    <div class="paper-journal">{journal_style}</div>
                    <div class="paper-date">발행일: {current_date}</div>
                </div>
                <h1 style="margin-bottom: 2rem;">{fake_paper['title']}</h1>
                <div style="margin-bottom: 2rem;">
                    <h2 style="font-size: 1.5rem; margin-bottom: 1rem;">초록</h2>
                    <p style="line-height: 1.6;">{fake_paper['abstract']}</p>
                </div>
                <div style="margin-bottom: 2rem;">
                    <h2 style="font-size: 1.5rem; margin-bottom: 1rem;">1. 서론</h2>
                    <p style="line-height: 1.6;">{fake_paper['introduction']}</p>
                </div>
                <div style="margin-bottom: 2rem;">
                    <h2 style="font-size: 1.5rem; margin-bottom: 1rem;">2. 이론적 배경</h2>
                    <p style="line-height: 1.6;">{fake_paper['background']}</p>
                </div>
                <div style="margin-bottom: 2rem;">
                    <h2 style="font-size: 1.5rem; margin-bottom: 1rem;">3. 연구 방법</h2>
                    <p style="line-height: 1.6;">{fake_paper['method']}</p>
                </div>
                <div style="margin-bottom: 2rem;">
                    <h2 style="font-size: 1.5rem; margin-bottom: 1rem;">4. 연구 결과</h2>
                    <p style="line-height: 1.6;">{fake_paper['results']}</p>
                </div>
                <div style="margin-bottom: 2rem;">
                    <h2 style="font-size: 1.5rem; margin-bottom: 1rem;">5. 결론</h2>
                    <p style="line-height: 1.6;">{fake_paper['conclusion']}</p>
                </div>
                <div style="margin-bottom: 2rem;">
                    <h2 style="font-size: 1.5rem; margin-bottom: 1rem;">참고문헌</h2>
                    <div style="font-family: 'Times New Roman', Times, serif;">
                    {references_html}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 논문 다운로드 버튼
            filename = f"generated_paper_{search_query[:30]}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"제목: {fake_paper['title']}\n\n")
                f.write(f"[초록]\n{fake_paper['abstract']}\n\n")
                f.write(f"[1. 서론]\n{fake_paper['introduction']}\n\n")
                f.write(f"[2. 이론적 배경]\n{fake_paper['background']}\n\n")
                f.write(f"[3. 연구 방법]\n{fake_paper['method']}\n\n")
                f.write(f"[4. 연구 결과]\n{fake_paper['results']}\n\n")
                f.write(f"[5. 결론]\n{fake_paper['conclusion']}\n\n")
                f.write(f"[참고문헌]\n{fake_paper['references']}\n")
            
            with open(filename, "r", encoding="utf-8") as f:
                st.download_button(
                    label="📥 논문 다운로드",
                    data=f.read(),
                    file_name=filename,
                    mime="text/plain"
                )
        else:
            # 실제 논문 검색
            with st.spinner("🔍 논문을 검색하고 있습니다..."):
                result = search_papers_by_keywords(search_query, DBPIA_API_KEY)
                
                if result['papers']:
                    st.success(f"✅ 총 {len(result['papers'])}개의 관련 논문을 찾았습니다!")
                    st.markdown(f"**검색 키워드:** {', '.join(result['keywords'])}")
                    
                    # 논문 목록 표시
                    for i, paper in enumerate(result['papers'], 1):
                        with st.container():
                            st.markdown("""
                            <style>
                                .paper-item {
                                    background-color: white;
                                    padding: 1.5rem;
                                    margin: 1rem 0;
                                    border-radius: 8px;
                                    border: 1px solid #FFD700;
                                }
                                .paper-title {
                                    color: #1a1a1a;
                                    font-size: 1.2rem;
                                    font-weight: bold;
                                    margin-bottom: 0.5rem;
                                }
                                .paper-meta {
                                    color: #666;
                                    font-size: 0.9rem;
                                    margin-bottom: 1rem;
                                }
                                .paper-abstract {
                                    color: #333;
                                    font-size: 1rem;
                                    line-height: 1.6;
                                }
                            </style>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="paper-item">
                                <div class="paper-title">📄 {i}. {paper['title']}</div>
                                <div class="paper-meta">
                                    상태: {'🔓 무료' if paper['is_free'] else '🔒 유료'}
                                    {f' | <a href="{paper["preview_url"]}" target="_blank">미리보기</a>' if paper.get('preview_url') else ''}
                                    {f' | <a href="{paper["link"]}" target="_blank">원문 보기</a>' if paper.get('link') else ''}
                                </div>
                                <div class="paper-abstract">
                                    {paper['abstract'] if paper.get('abstract') else '초록이 제공되지 않습니다.'}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.error("❌ 관련 논문을 찾지 못했습니다.")

with tabs[1]:
    st.markdown("오늘의 특선 괴논문이 이곳에 표시됩니다.")

with tabs[2]:
    st.markdown("최근 검색된 키워드들이 이곳에 표시됩니다.")
