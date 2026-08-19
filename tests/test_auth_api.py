import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_auth_api_success_english():
    # 1. 영문 페르소나 로그인 성공 테스트 및 세션 메타 검증
    expected_meta = {
        "healthcenter": {
            "role": "healthcenter",
            "scope": "sgg",
            "assigned_region": "서울특별시|양천구",
            "label": "양천구보건소 담당자"
        },
        "mohw": {
            "role": "mohw",
            "scope": "all",
            "assigned_region": "all",
            "label": "보건복지부 관리자"
        },
        "ncc": {
            "role": "ncc",
            "scope": "all",
            "assigned_region": "all",
            "label": "국립암센터 연구원"
        },
        "rcc": {
            "role": "rcc",
            "scope": "sido",
            "assigned_region": "서울특별시",
            "label": "지역암센터 담당자"
        }
    }
    
    for p, meta in expected_meta.items():
        payload = {"username": p, "password": p}
        response = client.post("/api/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == p
        assert data["role"] == meta["role"]
        assert data["scope"] == meta["scope"]
        assert data["assigned_region"] == meta["assigned_region"]
        assert data["label"] == meta["label"]

def test_auth_api_success_korean():
    # 2. 한글 페르소나 로그인 성공 테스트
    korean_personas = {
        "보건소": "healthcenter",
        "보건복지부": "mohw",
        "국립암센터": "ncc",
        "지역암센터": "rcc"
    }
    for k, role in korean_personas.items():
        payload = {"username": k, "password": k}
        response = client.post("/api/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == k
        assert data["role"] == role

def test_auth_api_fail_wrong_password():
    # 3. 비밀번호 불일치 실패 테스트
    payload = {"username": "healthcenter", "password": "wrongpassword"}
    response = client.post("/api/login", json=payload)
    assert response.status_code == 401
    assert "detail" in response.json()

def test_auth_api_fail_invalid_user():
    # 4. 미등록 사용자 실패 테스트
    payload = {"username": "unknown_user", "password": "unknown_user"}
    response = client.post("/api/login", json=payload)
    assert response.status_code == 401
