import faiss
import numpy as np
from openai import OpenAI
import tiktoken
import json
import os
from typing import List, Dict, Any

class PaperVectorStore:
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.papers = []
        self.client = OpenAI()
        self.encoding = tiktoken.encoding_for_model("text-embedding-3-small")
        
    def add_papers(self, papers: List[Dict[str, Any]]):
        """논문을 벡터 저장소에 추가합니다."""
        texts = []
        for paper in papers:
            if paper.get('abstract'):
                # 초록에서 핵심 내용 추출
                abstract = paper['abstract']
                # 초록을 문장 단위로 분리
                sentences = abstract.split('.')
                # 핵심 문장 선택 (처음 3문장과 마지막 2문장)
                key_sentences = sentences[:3] + sentences[-2:] if len(sentences) > 5 else sentences
                # 핵심 내용으로 구성
                key_content = '. '.join(key_sentences).strip()
                texts.append(key_content)
                self.papers.append(paper)
        
        if not texts:
            return
        
        # OpenAI Embedding API를 사용하여 텍스트를 벡터로 변환
        embeddings = []
        for text in texts:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            embeddings.append(response.data[0].embedding)
        
        # FAISS 인덱스에 벡터 추가
        vectors = np.array(embeddings).astype('float32')
        self.index.add(vectors)
    
    def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """쿼리와 가장 유사한 논문을 검색합니다."""
        # 쿼리를 벡터로 변환
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_vector = np.array([response.data[0].embedding]).astype('float32')
        
        # 유사한 벡터 검색 (k를 2배로 증가)
        distances, indices = self.index.search(query_vector, k * 2)
        
        # 결과 반환 (거리 기반 필터링 추가)
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.papers) and distance < 0.5:  # 거리 임계값 추가
                results.append(self.papers[idx])
            if len(results) >= k:  # 원하는 수의 결과에 도달하면 중단
                break
        
        return results
    
    def get_context_within_token_limit(self, papers: List[Dict[str, Any]], max_tokens: int) -> str:
        """
        주어진 논문 목록에서 토큰 제한 내에서 컨텍스트를 구성합니다.
        
        Args:
            papers: 논문 목록
            max_tokens: 최대 토큰 수
            
        Returns:
            구성된 컨텍스트 문자열
        """
        context = []
        current_tokens = 0
        
        for paper in papers:
            # 각 논문의 초록에서 핵심 내용 추출
            abstract = paper.get('abstract', '')
            if not abstract:
                continue
                
            # 초록을 문장 단위로 분리
            sentences = abstract.split('.')
            # 핵심 문장 선택 (처음 2문장과 마지막 1문장으로 더 줄임)
            key_sentences = sentences[:2] + sentences[-1:] if len(sentences) > 3 else sentences
            # 핵심 내용으로 구성
            key_content = '. '.join(key_sentences).strip()
            
            # 핵심 내용의 토큰 수 계산
            key_tokens = len(self.encoding.encode(key_content))
            
            # 토큰 제한을 초과하지 않는 경우에만 추가
            if current_tokens + key_tokens <= max_tokens:
                context.append(f"제목: {paper.get('title', '')}\n핵심 내용: {key_content}\n")
                current_tokens += key_tokens
            else:
                break
        
        return "\n".join(context)
    
    def save(self, path: str):
        """벡터 저장소를 파일로 저장합니다."""
        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # FAISS 인덱스 저장
        faiss.write_index(self.index, f"{path}.index")
        
        # 논문 메타데이터 저장
        with open(f"{path}.json", 'w', encoding='utf-8') as f:
            json.dump(self.papers, f, ensure_ascii=False, indent=2)
        
        # 검색 ID 저장
        with open(f"{path}.id", 'w', encoding='utf-8') as f:
            f.write(os.path.basename(path).split('_')[-1])
    
    @classmethod
    def load(cls, path: str) -> 'PaperVectorStore':
        """파일에서 벡터 저장소를 로드합니다."""
        store = cls()
        
        # FAISS 인덱스 로드
        if os.path.exists(f"{path}.index"):
            store.index = faiss.read_index(f"{path}.index")
        
        # 논문 메타데이터 로드
        if os.path.exists(f"{path}.json"):
            with open(f"{path}.json", 'r', encoding='utf-8') as f:
                store.papers = json.load(f)
        
        return store

    def cleanup_old_stores(self, max_age_hours: int = 24):
        """오래된 벡터 저장소를 정리합니다."""
        import time
        import glob
        
        # vectorstore 디렉토리의 모든 파일 목록 가져오기
        files = glob.glob("vectorstore/*")
        
        for file in files:
            # 파일의 마지막 수정 시간 확인
            file_age = time.time() - os.path.getmtime(file)
            age_hours = file_age / 3600
            
            # 지정된 시간보다 오래된 파일 삭제
            if age_hours > max_age_hours:
                try:
                    os.remove(file)
                except Exception as e:
                    print(f"Error deleting {file}: {e}") 