from openai import OpenAI
from typing import List, Dict
from .vector_store import PaperVectorStore
import os

def generate_fake_paper(
    vector_store: PaperVectorStore,
    query: str,
    max_tokens: int = 4096
) -> Dict[str, str]:
    """
    벡터 저장소에서 유사한 논문을 검색하고, 이를 기반으로 새로운 논문을 생성합니다.
    
    Args:
        vector_store: 논문 벡터 저장소
        query: 검색 쿼리
        max_tokens: 최대 토큰 수
        
    Returns:
        생성된 논문의 각 섹션을 포함하는 딕셔너리
    """
    client = OpenAI()
    
    # 유사한 논문 검색
    similar_papers = vector_store.search_similar(query, k=5)
    
    # 토큰 제한 내에서 컨텍스트 구성
    context = vector_store.get_context_within_token_limit(similar_papers, max_tokens // 2)
    
    # 프롬프트 구성
    prompt = f"""다음은 주제 '{query}'와 관련된 논문 스타일의 텍스트입니다.  
이를 바탕으로 **새롭고 창의적인 학술 논문**을 작성해주세요.  
논문은 다음 마크다운 형식을 따라야 합니다:

# [논문 제목]

## 초록
목적, 방법, 결과, 결론을 요약 (200~300자, 학술적 톤 유지)

## 1. 서론
연구의 배경과 동기를 설명하되, 현실과 살짝 엉뚱한 세계관이 섞이도록

## 2. 이론적 배경
실제 연구를 기반으로 하되, 유쾌한 문헌 예시나 비유 포함 가능

## 3. 연구 방법
현실적인 연구 방법을 사용하되, 다소 엉뚱한 요소를 함께 기술할 수 있음

## 4. 연구 결과
실제 분석 결과처럼 보이게 작성하되, 독특한 인사이트나 유머도 반영

## 5. 결론
의의와 한계를 정리하고, 향후 연구 방향을 제시

## 참고문헌
연예인, 애니메이션 캐릭터 등을 이용하여 가상의 유쾌하고 독특한 문헌들을 작성해주세요

참고 논문의 핵심 내용:
{context}

지침:
1. 실제로 연구 가능할 법한 주제를 선택하되, 창의적이고 엉뚱한 접근도 허용됩니다
2. 현실에 기반한 방법론을 사용하되, 엉뚱한 요소와 혼합해 표현해도 좋습니다
3. 전체적으로는 학술적인 어조를 유지하되, 적절한 위트나 비유를 포함할 수 있습니다
4. 참고문헌은 논문의 분위기를 반영하며, 캐릭터, 음식점, 연예인, 밈 등을 활용해 가상으로 구성해주세요

위 형식에 맞춰 새롭고 독창적인 논문을 작성해주세요.
각 섹션은 반드시 내용을 포함해야 하며, 섹션 제목과 내용을 명확히 구분해주세요."""

    # GPT-4.1-nano 모델로 논문 생성
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "You are a professional academic researcher with a good sense of humor. Write a detailed academic paper in Korean with fun references."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=max_tokens
    )
    
    # 응답 파싱
    content = response.choices[0].message.content
    
    # 각 섹션 추출
    sections = {
        "title": "",
        "abstract": "",
        "introduction": "",
        "background": "",
        "method": "",
        "results": "",
        "conclusion": "",
        "references": ""
    }
    
    # 섹션 분리
    current_section = None
    current_content = []
    
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # 제목 찾기 (# 으로 시작하는 첫 번째 줄)
        if line.startswith('# '):
            sections['title'] = line.replace('# ', '').strip()
            i += 1
            continue
        
        # 초록 찾기
        if line.startswith('## 초록'):
            i += 1
            while i < len(lines):
                line = lines[i].strip()
                if not line or line.startswith('## '):
                    break
                sections['abstract'] += line + '\n'
                i += 1
            continue
        
        # 서론 찾기
        if line.startswith('## 1.') or line.startswith('## 서론'):
            i += 1
            while i < len(lines):
                line = lines[i].strip()
                if not line or line.startswith('## '):
                    break
                sections['introduction'] += line + '\n'
                i += 1
            continue
        
        # 이론적 배경 찾기
        if line.startswith('## 2.') or line.startswith('## 이론'):
            i += 1
            while i < len(lines):
                line = lines[i].strip()
                if not line or line.startswith('## '):
                    break
                sections['background'] += line + '\n'
                i += 1
            continue
        
        # 연구 방법 찾기
        if line.startswith('## 3.') or line.startswith('## 연구 방법'):
            i += 1
            while i < len(lines):
                line = lines[i].strip()
                if not line or line.startswith('## '):
                    break
                sections['method'] += line + '\n'
                i += 1
            continue
        
        # 연구 결과 찾기
        if line.startswith('## 4.') or line.startswith('## 연구 결과'):
            i += 1
            while i < len(lines):
                line = lines[i].strip()
                if not line or line.startswith('## '):
                    break
                sections['results'] += line + '\n'
                i += 1
            continue
        
        # 결론 찾기
        if line.startswith('## 5.') or line.startswith('## 결론'):
            i += 1
            while i < len(lines):
                line = lines[i].strip()
                if not line or line.startswith('## '):
                    break
                sections['conclusion'] += line + '\n'
                i += 1
            continue
        
        # 참고문헌 찾기
        if line.startswith('## 참고문헌'):
            i += 1
            while i < len(lines):
                line = lines[i].strip()
                if not line or line.startswith('## '):
                    break
                sections['references'] += line + '\n'
                i += 1
            continue
        
        i += 1
    
    # 섹션 내용 정리
    for section in sections:
        sections[section] = sections[section].strip()
        if not sections[section]:
            sections[section] = f"{section} 섹션이 비어있습니다. 다시 시도해주세요."
    
    # 디버깅을 위한 원본 응답 출력
    print("\n=== 원본 응답 ===")
    print(content)
    print("\n=== 파싱된 섹션 ===")
    for section, content in sections.items():
        print(f"\n--- {section} ---")
        print(content)
    
    return sections
