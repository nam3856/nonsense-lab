from backend.dbpia_handler import fetch_real_abstract
import os
import re
from typing import List, Dict, Any
from openai import OpenAI

def extract_keywords_with_openai(query: str) -> List[str]:
    """
    OpenAI를 사용하여 쿼리에서 중요한 키워드 2-3개를 추출합니다.
    
    Args:
        query: 사용자가 입력한 검색 쿼리
        
    Returns:
        추출된 키워드 리스트
    """
    client = OpenAI()
    
    prompt = f"""다음 연구 주제에서 가장 중요한 키워드 2-3개만 추출해주세요.
키워드는 연구의 핵심 주제를 나타내는 명사여야 합니다.
각 키워드는 쉼표로 구분하여 한 줄로 작성해주세요.

연구 주제: {query}"""

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "You are a helpful research assistant. Extract only the most important 2-3 keywords from the given research topic."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=100
    )
    
    keywords = response.choices[0].message.content.strip().split(',')
    keywords = [kw.strip() for kw in keywords if kw.strip()]
    
    return keywords

def search_papers_by_keywords(query: str, api_key: str) -> Dict[str, Any]:
    """
    주어진 쿼리에서 키워드를 추출하고, 각 키워드에 대해 논문을 검색합니다.
    
    Args:
        query: 사용자가 입력한 검색 쿼리
        api_key: DBpia API 키
        
    Returns:
        검색 결과와 키워드를 포함하는 딕셔너리
    """
    # OpenAI를 사용하여 중요한 키워드 추출
    keywords = extract_keywords_with_openai(query)
    
    # 각 키워드에 대해 논문 검색
    papers = []
    for keyword in keywords:
        papers.extend(fetch_real_abstract(keyword, api_key))
    
    # 중복 제거
    seen_titles = set()
    unique_papers = []
    for paper in papers:
        if paper['title'] not in seen_titles:
            seen_titles.add(paper['title'])
            unique_papers.append(paper)
    
    return {
        'papers': unique_papers,
        'keywords': keywords,
        'original_query': query
    }