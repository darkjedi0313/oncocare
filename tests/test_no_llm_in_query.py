import os

def test_no_llm_imports_in_query_router():
    query_router_path = "api/routers/query.py"
    
    # query_router.py 파일이 존재하는지 검증 (아직 미생성 상태면 Pass 처리할 수도 있으나, 
    # 구현 시점에는 무조건 있어야 하므로 존재 확인 포함)
    assert os.path.exists(query_router_path), f"{query_router_path} 파일이 없습니다."
    
    with open(query_router_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # 금지된 키워드 목록
    # api/llm, langchain 관련 모듈 import 전면 금지
    forbidden_keywords = [
        "import llm",
        "from api import llm",
        "api.llm",
        "langchain",
        "google-generativeai",
        "google.generativeai"
    ]
    
    # 대소문자 구분 없이 검사하기 위해 소문자로 변환
    content_lower = content.lower()
    
    for keyword in forbidden_keywords:
        assert keyword not in content_lower, f"금지된 키워드 '{keyword}'가 {query_router_path}에서 검출되었습니다!"
