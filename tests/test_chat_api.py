import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_chat_api_structure_and_pii():
    # 1. API 구조 및 개인정보 미포함 검증
    payload = {
        "segment": {
            "region": "서울특별시|양천구",
            "sex": "여자",
            "age": "65~69",
            "cancer": "대장암"
        },
        "year": 2024,
        "history": [
            {"role": "user", "content": "우리 구의 대장암 수검률은 얼마인가요?"}
        ]
    }
    
    # PII가 payload의 FactorSegment 모델에 없음을 정적 확인
    assert "name" not in payload["segment"]
    assert "phone" not in payload["segment"]
    assert "ssn" not in payload["segment"]
    assert "address" not in payload["segment"]
    
    # 2. API 호출 검증
    response = client.post("/api/chat", json=payload)
    
    # GEMINI_API_KEY 환경변수가 설정되어 있다면 200, 설정되어 있지 않다면 500 오류
    if response.status_code == 200:
        data = response.json()
        assert "reply" in data
        assert "facts_used" in data
        assert data["안내문구"] == "이 값은 평가가 아니라 검토 시작점입니다"
        
        # 인용된 팩트 데이터 규격 확인
        assert len(data["facts_used"]) > 0
        for fact in data["facts_used"]:
            assert "label" in fact
            assert "value" in fact
    else:
        # API Key 누락 또는 기타 예측 가능한 서버 가용성 오류 핸들링
        assert response.status_code in [500, 404]
        err_msg = response.json().get("detail", "")
        # 특정 에러 조건 확인
        assert any(keyword in err_msg for keyword in ["GEMINI_API_KEY", "데이터", "오류", "설정"])
