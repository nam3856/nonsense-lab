# backend/dbpia_handler.py
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

def fetch_real_abstract(query: str, api_key: str):
    url = "https://api.dbpia.co.kr/v2/search/search.xml"
    params = {
        "key": api_key,
        "searchall": query,
        "target": "se",
        "pagecount": 20  # 무료 논문을 찾기 위해 더 많은 결과를 가져옴
    }

    response = requests.get(url, params=params)
    root = ET.fromstring(response.content)
    
    papers = []
    try:
        # 모든 item 요소를 찾아서 처리
        for item in root.findall(".//item"):
            title = item.findtext("title") or "(제목 없음)"
            link = item.findtext("link_url") or "https://www.dbpia.co.kr"
            is_free = item.findtext("free_yn") == "Y"
            has_preview = item.findtext("preview_yn") == "Y"
            preview_url = item.findtext("preview") if has_preview else None
            
            paper_info = {
                "title": title.replace("<!HS>", "").replace("<!HE>", ""),  # 하이라이트 태그 제거
                "link": link,
                "is_free": is_free,
                "has_preview": has_preview,
                "preview_url": preview_url,
                "abstract": None
            }
            
            # 무료 논문이거나 미리보기가 있는 경우에만 시도
            if is_free or has_preview:
                try:
                    detail_response = requests.get(link)
                    if detail_response.status_code == 200:
                        soup = BeautifulSoup(detail_response.text, 'html.parser')
                        abstract_div = soup.find('div', class_='abstractTxt')
                        if abstract_div and abstract_div.text.strip() and abstract_div.text.strip() != "등록된 정보가 없습니다.":
                            paper_info["abstract"] = abstract_div.text.strip()
                            papers.append(paper_info)
                            print(f"✅ {'무료' if is_free else '미리보기'} 논문 발견: {title}")
                            
                            # 10개가 되면 중단
                            if len(papers) >= 5:
                                break
                except Exception as e:
                    print(f"❌ 상세 페이지 파싱 실패: {link}")
                    continue
                
        return papers
    except Exception as e:
        print(f"❌ 파싱 실패: {e}")
        return []
