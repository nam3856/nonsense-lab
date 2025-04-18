import os
import streamlit as st
import random
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Page configuration
st.set_page_config(
    page_title="FakePaperia",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
            # Fun loading animation with random messages
            loading_placeholder = st.empty()
            for i in range(5):  # Show 5 different loading messages
                with loading_placeholder:
                    st.markdown(f"""
                    <div class="loading-container">
                        <h3>{random.choice(LOADING_MESSAGES)}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(1)  # Show each message for 1 second

            # Generate paper
            response = openai.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": "You are an academic paper generator that writes in Korean. Create a formal academic paper with proper structure including title, abstract, introduction, methodology, results, discussion, and conclusion. Make it sound professional but include some subtle humor and interesting twists."},
                    {"role": "user", "content": f"Generate an academic paper about: {search_query}"}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            # Clear loading animation
            loading_placeholder.empty()
            
            # Add fun paper header
            journal_style = random.choice(PAPER_STYLES)
            current_date = time.strftime("%Y년 %m월 %d일")
            
            st.markdown(f"""
            <div class="paper-container">
                <div class="paper-header">
                    <div class="paper-journal">{journal_style}</div>
                    <div class="paper-date">발행일: {current_date}</div>
                </div>
                {response.choices[0].message.content}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("일반 논문 검색 기능은 준비 중입니다.")

with tabs[1]:
    st.markdown("오늘의 특선 괴논문이 이곳에 표시됩니다.")

with tabs[2]:
    st.markdown("최근 검색된 키워드들이 이곳에 표시됩니다.")
