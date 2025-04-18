import os
import streamlit as st
import random
import time
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from backend.backend_utils import search_papers_by_keywords
from backend.openai_fakegen import generate_fake_paper
from backend.vector_store import PaperVectorStore
from backend.reaction_utils import generate_reaction, get_reaction_gif

# Load environment variables
load_dotenv()
DBPIA_API_KEY = os.getenv("DBPIA_API_KEY")

# Constants
PAPERS_STORAGE_FILE = "generated_papers.json"
KEYWORDS_STORAGE_FILE = "search_keywords.json"

# Initialize storage
def init_storage():
    if not os.path.exists(PAPERS_STORAGE_FILE):
        with open(PAPERS_STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)
    
    if not os.path.exists(KEYWORDS_STORAGE_FILE):
        with open(KEYWORDS_STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)

def save_generated_paper(paper_data, search_query):
    try:
        with open(PAPERS_STORAGE_FILE, "r", encoding="utf-8") as f:
            papers = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        papers = []
    
    # Add metadata to paper
    paper_data["generated_at"] = datetime.now().isoformat()
    paper_data["search_query"] = search_query
    paper_data["paper_id"] = str(uuid.uuid4())
    
    # Add to papers list
    papers.append(paper_data)
    
    # Save back to file
    with open(PAPERS_STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    
    return paper_data["paper_id"]

def load_generated_papers():
    try:
        with open(PAPERS_STORAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_search_keyword(keyword):
    try:
        with open(KEYWORDS_STORAGE_FILE, "r", encoding="utf-8") as f:
            keywords = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        keywords = []
    
    # Add new keyword with timestamp
    keyword_data = {
        "keyword": keyword,
        "searched_at": datetime.now().isoformat()
    }
    
    # Remove duplicate if exists
    keywords = [k for k in keywords if k["keyword"] != keyword]
    
    # Add new keyword at the beginning
    keywords.insert(0, keyword_data)
    
    # Keep only last 50 keywords
    keywords = keywords[:50]
    
    # Save back to file
    with open(KEYWORDS_STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(keywords, f, ensure_ascii=False, indent=2)

def load_search_keywords():
    try:
        with open(KEYWORDS_STORAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Initialize storage on startup
init_storage()

# Session state for search query
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

def update_search_query(keyword):
    current_query = st.session_state.search_query.strip()
    if current_query:
        st.session_state.search_query = f"{current_query}, {keyword}"
    else:
        st.session_state.search_query = keyword

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
        placeholder="예시: 이어폰 줄꼬임에 대한 심리학적 분석",
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

# Save keyword when search button is clicked
if search_button and search_query:
    save_search_keyword(search_query)

# Category Tabs
tabs = st.tabs(["AI 검색", "📝 내 논문...인 듯?", "최근 검색 키워드"])

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
            
            # 리액션 생성 및 GIF 가져오기
            reaction = generate_reaction(fake_paper['title'], fake_paper['abstract'])
            gif_url = get_reaction_gif(reaction)

            # 논문 제목과 헤더
            st.markdown(f"""
            <div class="paper-container">
                <div class="paper-header">
                    <div class="paper-journal">{journal_style}</div>
                    <div class="paper-date">발행일: {current_date}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 논문 제목
            st.markdown(f"# {fake_paper['title']}")
            
            # 초록
            st.markdown("## 초록")
            st.markdown(fake_paper['abstract'])
            
            # 서론
            st.markdown("## 1. 서론")
            st.markdown(fake_paper['introduction'])
            
            # 이론적 배경
            st.markdown("## 2. 이론적 배경")
            st.markdown(fake_paper['background'])
            
            # 연구 방법
            st.markdown("## 3. 연구 방법")
            st.markdown(fake_paper['method'])
            
            # 연구 결과
            st.markdown("## 4. 연구 결과")
            st.markdown(fake_paper['results'])
            
            # 결론
            st.markdown("## 5. 결론")
            st.markdown(fake_paper['conclusion'])
            
            # 참고문헌
            st.markdown("## 참고문헌")
            references = fake_paper['references'].split('\n')
            for ref in references:
                if ref.strip():
                    st.markdown(f"- {ref}")

            # 스타일 적용
            st.markdown("""
            <style>
                .paper-container {
                    background-color: white;
                    padding: 2rem;
                    margin-bottom: 2rem;
                    border-radius: 8px;
                }
                .paper-header {
                    text-align: center;
                    margin-bottom: 2rem;
                }
                .paper-journal {
                    font-size: 1.2rem;
                    color: #666;
                    margin-bottom: 0.5rem;
                }
                .paper-date {
                    color: #888;
                }
                h1 {
                    font-size: 2rem;
                    margin-bottom: 2rem;
                    text-align: center;
                }
                h2 {
                    font-size: 1.5rem;
                    margin: 2rem 0 1rem 0;
                    color: #333;
                }
                p {
                    line-height: 1.6;
                    color: #444;
                    margin-bottom: 1rem;
                }
            </style>
            """, unsafe_allow_html=True)

            # 리액션 섹션 (논문 내용 아래에 표시)
            st.markdown("""
            <div style='background-color: #f8f8f8; padding: 2rem; border-radius: 8px; margin: 2rem 0; text-align: center; border: 1px solid #FFD700;'>
                <h3 style='margin-bottom: 1rem; color: #333;'>🤖 AI의 리액션</h3>
                <p style='font-size: 1.2rem; margin-bottom: 1.5rem; color: #666;'>{}</p>
                {}
            </div>
            """.format(
                reaction,
                f'<img src="{gif_url}" style="max-width: 300px; border-radius: 8px; margin: 0 auto; display: block;" alt="Reaction GIF">' if gif_url else ''
            ), unsafe_allow_html=True)

            # Save generated paper after generation
            paper_data = {
                "title": fake_paper["title"],
                "abstract": fake_paper["abstract"],
                "introduction": fake_paper["introduction"],
                "background": fake_paper["background"],
                "method": fake_paper["method"],
                "results": fake_paper["results"],
                "conclusion": fake_paper["conclusion"],
                "references": fake_paper["references"]
            }
            save_generated_paper(paper_data, search_query)

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
                    mime="text/plain",
                    key=f"download_new_{str(uuid.uuid4())}"
                )
        else:
            # 실제 논문 검색
            with st.spinner("🔍 논문을 검색하고 있습니다..."):
                result = search_papers_by_keywords(search_query, DBPIA_API_KEY)
                
                if result['papers']:
                    st.success(f"✅ 총 {len(result['papers'])}개의 관련 논문을 찾았습니다!")
                    st.markdown(f"**검색 키워드:** {', '.join(result['keywords'])}")
                    
                    # 논문 목록 표시
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
                            margin-bottom: 0.8rem;
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
                        .paper-link {
                            color: #1E88E5;
                            text-decoration: none;
                            margin-left: 0.5rem;
                        }
                        .paper-link:hover {
                            text-decoration: underline;
                        }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    for i, paper in enumerate(result['papers'], 1):
                        # 메타 정보 구성
                        meta_parts = []
                        meta_parts.append('🔓 무료' if paper['is_free'] else '🔒 유료')
                        if paper.get('preview_url'):
                            meta_parts.append(f'<a href="{paper["preview_url"]}" target="_blank" class="paper-link">미리보기</a>')
                        if paper.get('link'):
                            meta_parts.append(f'<a href="{paper["link"]}" target="_blank" class="paper-link">원문 보기</a>')
                        
                        st.markdown(f"""
                        <div class="paper-item">
                            <div class="paper-title">📄 {i}. {paper['title']}</div>
                            <div class="paper-meta">{' | '.join(meta_parts)}</div>
                            <div class="paper-abstract">
                                {paper.get('abstract', '초록이 제공되지 않습니다.')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error("❌ 관련 논문을 찾지 못했습니다.")

with tabs[1]:
    st.markdown("## 📚 내가 지금까지 생성한 괴논문 모음")
    
    # Load all generated papers
    generated_papers = load_generated_papers()
    
    if not generated_papers:
        st.info("아직 생성된 논문이 없습니다. AI 검색 탭에서 논문을 생성해보세요!")
    else:
        # Sort papers by generation date (newest first)
        generated_papers.sort(key=lambda x: x["generated_at"], reverse=True)
        
        for paper in generated_papers:
            with st.expander(f"📄 {paper['title']} ({datetime.fromisoformat(paper['generated_at']).strftime('%Y-%m-%d %H:%M')})"):
                st.markdown(f"**검색어:** {paper['search_query']}")
                
                # Paper content tabs
                paper_tabs = st.tabs(["초록", "본문", "AI 리액션"])
                
                with paper_tabs[0]:
                    st.markdown(paper["abstract"])
                
                with paper_tabs[1]:
                    st.markdown("### 1. 서론")
                    st.markdown(paper["introduction"])
                    st.markdown("### 2. 이론적 배경")
                    st.markdown(paper["background"])
                    st.markdown("### 3. 연구 방법")
                    st.markdown(paper["method"])
                    st.markdown("### 4. 연구 결과")
                    st.markdown(paper["results"])
                    st.markdown("### 5. 결론")
                    st.markdown(paper["conclusion"])
                    st.markdown("### 참고문헌")
                    references = paper["references"].split('\n')
                    for ref in references:
                        if ref.strip():
                            st.markdown(f"- {ref}")
                
                with paper_tabs[2]:
                    # Generate real-time reaction
                    reaction = generate_reaction(paper["title"], paper["abstract"])
                    gif_url = get_reaction_gif(reaction)
                    
                    st.markdown(f"### 🤖 AI의 리액션")
                    st.markdown(reaction)
                    if gif_url:
                        st.image(gif_url, width=300)
                
                # Download button
                paper_content = f"""제목: {paper['title']}\n\n
[초록]\n{paper['abstract']}\n\n
[1. 서론]\n{paper['introduction']}\n\n
[2. 이론적 배경]\n{paper['background']}\n\n
[3. 연구 방법]\n{paper['method']}\n\n
[4. 연구 결과]\n{paper['results']}\n\n
[5. 결론]\n{paper['conclusion']}\n\n
[참고문헌]\n{paper['references']}"""
                
                st.download_button(
                    label="📥 논문 다운로드",
                    data=paper_content,
                    file_name=f"generated_paper_{paper['search_query'][:30]}.txt",
                    mime="text/plain",
                    key=f"download_stored_{paper['paper_id']}"
                )

with tabs[2]:
    st.markdown("## 🔍 최근 검색 키워드")
    
    # Load and display recent keywords
    keywords = load_search_keywords()
    
    if not keywords:
        st.info("아직 검색 기록이 없습니다. 검색을 시작해보세요!")
    else:
        st.markdown("""
        <style>
        .keyword-cloud {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 1rem 0;
        }
        .keyword-item {
            background-color: #FFD700;
            color: black;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            cursor: pointer;
            transition: background-color 0.3s;
            text-decoration: none;
            display: inline-block;
            margin: 0.25rem;
        }
        .keyword-item:hover {
            background-color: #FFE55C;
        }
        .keyword-date {
            color: #666;
            font-size: 0.8rem;
            margin-left: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="keyword-cloud">', unsafe_allow_html=True)
        
        for keyword_data in keywords:
            keyword = keyword_data["keyword"]
            searched_at = datetime.fromisoformat(keyword_data["searched_at"]).strftime("%Y-%m-%d %H:%M")
            
            # Create clickable keyword button
            if st.button(
                f"🔍 {keyword}",
                key=f"keyword_{keyword_data['searched_at']}",
                help=f"마지막 검색: {searched_at}"
            ):
                update_search_query(keyword)
                st.experimental_rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
