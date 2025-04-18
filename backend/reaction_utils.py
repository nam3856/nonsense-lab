from openai import OpenAI
import requests
import random
import os
from dotenv import load_dotenv

load_dotenv()
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")

def generate_reaction(paper_title, paper_abstract):
    """논문에 대한 재미있는 리액션을 생성합니다."""
    client = OpenAI()
    
    prompt = f"""다음 논문의 제목과 초록을 읽고, 이에 대한 재미있고 위트있는 리액션을 한 문장으로 만들어주세요.
    재미있거나, 황당하거나, 의아하거나, 놀라운 반응이면 좋습니다.
    
    제목: {paper_title}
    초록: {paper_abstract}
    
    예시:
    - "도대체 뭘 읽은 거지?"
    - "이게 진짜 논문이라고요?"
    - "교수님이 보시면 기절하실 것 같아요..."
    - "이런 연구를 하다니 당신은 천재인가요?"
    
    위와 같은 스타일로, 논문을 읽은 후의 재미있는 리액션을 한 문장으로 만들어주세요.
    단, 반드시 한국어로 작성해주세요."""
    
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "You are a witty academic reviewer who loves to make funny reactions to papers."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=100
    )
    
    return response.choices[0].message.content.strip().strip('"')

def get_reaction_gif(reaction_text):
    """리액션 텍스트를 기반으로 적절한 GIF를 검색합니다."""
    try:
        # 한글 리액션을 영어 감정/상황 키워드로 매핑
        emotion_keywords = {
            "뭘": "confused",
            "기절": "faint",
            "천재": "genius",
            "놀랍": "surprised",
            "황당": "shocked",
            "웃": "laugh",
            "대박": "amazing",
            "미쳤": "crazy",
            "헐": "omg",
            "어이": "speechless"
        }
        
        # 리액션 텍스트에서 키워드 찾기
        search_query = "confused"  # 기본값
        for kr_word, en_word in emotion_keywords.items():
            if kr_word in reaction_text:
                search_query = en_word
                break
        
        # GIPHY API 호출
        url = f"https://api.giphy.com/v1/gifs/search"
        params = {
            "api_key": GIPHY_API_KEY,
            "q": search_query,
            "limit": 10,
            "rating": "g"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if data["data"]:
            # 랜덤하게 하나의 GIF 선택
            gif = random.choice(data["data"])
            return gif["images"]["original"]["url"]
            
    except Exception as e:
        print(f"GIPHY API 호출 중 오류 발생: {e}")
        return None
    
    return None 