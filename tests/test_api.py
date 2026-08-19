import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to OncoCare API Server"}

def test_api_summary():
    # 양천구 2024년 데이터가 정상 로드되었는지 확인하는 summary 테스트
    response = client.get("/api/summary?region=서울특별시|양천구&year=2024")
    assert response.status_code == 200
    data = response.json()
    
    # 스키마 구성 검증
    assert "지역명" in data
    assert "연도" in data
    assert "통합_수검률" in data
    assert "전국_순위" in data
    assert "전체_시군구수" in data
    assert "미수검_인원" in data
    assert "암종별_현황" in data
    assert "우선_대상_top3" in data
    assert data["안내문구"] == "이 값은 평가가 아니라 검토 시작점입니다"
    
    assert data["지역명"] == "양천구"
    assert data["연도"] == 2024

def test_api_priority():
    # 2024년 우선순위 목록 조회 테스트
    response = client.get("/api/priority?year=2024")
    assert response.status_code == 200
    data = response.json()
    
    assert "연도" in data
    assert "총_세그먼트수" in data
    assert "목록" in data
    assert data["연도"] == 2024
    
    # 목록이 존재한다면, 회복여지 내림차순 정렬 여부 검증
    items = data["목록"]
    if len(items) > 1:
        for i in range(len(items) - 1):
            assert items[i]["회복여지"] >= items[i+1]["회복여지"], "회복여지 내림차순 정렬이 깨졌습니다!"
            assert items[i]["연령"] not in ["75~79", "80~84", "85이상"], "75세 이상 세그먼트가 포함되어 있습니다!"
            assert items[i]["회복여지"] >= 300, "회복여지가 300명 미만인 세그먼트가 포함되어 있습니다!"

def test_api_compare():
    # compare API 조회 테스트
    response = client.get("/api/compare?region=서울특별시|양천구&gender=여자&age=65~69&cancer=대장암&year=2024")
    assert response.status_code == 200
    data = response.json()
    
    assert "연도" in data
    assert "지역명" in data
    assert "성별" in data
    assert "연령" in data
    assert "암종" in data
    assert "실제_수검률" in data
    assert "기대치" in data
    assert "잔차" in data
    assert "유사_평균" in data
    assert "유사_최소" in data
    assert "유사_최대" in data
    assert "유사_SE" in data
    assert "유사_지역목록" in data
    
    assert data["지역명"] == "양천구"
    assert data["성별"] == "여자"
    assert data["연령"] == "65~69"
    assert data["암종"] == "대장암"
    assert len(data["유사_지역목록"]) == 20

def test_api_determinism():
    # AGENTS.md: 동일 요청 10회 반복 시 응답 동일 (결정성) 검증
    urls = [
        "/api/summary?region=서울특별시|양천구&year=2024",
        "/api/priority?year=2024",
        "/api/compare?region=서울특별시|양천구&gender=여자&age=65~69&cancer=대장암&year=2024"
    ]
    
    for url in urls:
        responses = [client.get(url).json() for _ in range(10)]
        first_resp = responses[0]
        for r in responses[1:]:
            assert r == first_resp, f"비결정성 발생! URL: {url}"

def test_api_factors():
    # factors API 조회 테스트
    response = client.get("/api/factors?region=서울특별시|양천구&sex=여자&age=65~69&cancer=대장암&year=2024")
    assert response.status_code == 200
    data = response.json()
    
    assert "segment" in data
    assert "changeable" in data
    assert "fixed" in data
    assert "strata_table" in data
    assert "cautions" in data
    
    assert data["segment"]["region"] == "서울특별시|양천구"
    assert data["segment"]["sex"] == "여자"
    assert data["segment"]["age"] == "65~69"
    assert data["segment"]["cancer"] == "대장암"
    
    # changeable 요인 검사
    assert len(data["changeable"]) > 0
    assert "관내" in data["changeable"][0]["factor"]
    assert "대장내시경" in data["changeable"][0]["factor"]
    
    # fixed 요인 검사
    fixed_factors = [f["factor"] for f in data["fixed"]]
    assert "연령 구조" in fixed_factors
    assert "소득 수준" in fixed_factors
    
    # strata_table 검사
    assert len(data["strata_table"]) > 0
    for row in data["strata_table"]:
        assert "stratum" in row
        assert "absent" in row
        assert "present" in row
        assert "diff" in row
        assert "absent_target" in row

def test_api_factors_determinism():
    url = "/api/factors?region=서울특별시|양천구&sex=여자&age=65~69&cancer=대장암&year=2024"
    responses = [client.get(url).json() for _ in range(10)]
    first_resp = responses[0]
    for r in responses[1:]:
        assert r == first_resp, f"Factors 비결정성 발생!"

def test_api_actions():
    # actions API 조회 테스트
    response = client.get("/api/actions?region=서울특별시|양천구&sex=여자&age=65~69&cancer=대장암&year=2024")
    assert response.status_code == 200
    data = response.json()
    
    assert "segment" in data
    assert "rate" in data
    assert "rule_applied" in data
    assert "actions" in data
    assert "survey_questions" in data
    
    assert data["segment"]["region"] == "서울특별시|양천구"
    assert data["segment"]["sex"] == "여자"
    assert data["segment"]["age"] == "65~69"
    assert data["segment"]["cancer"] == "대장암"
    
    # actions에 카드가 2개 이상 들어있는지 확인
    assert len(data["actions"]) >= 2
    # survey_questions에 질문이 3개 들어있는지 확인
    assert len(data["survey_questions"]) == 3

def test_api_sample():
    # sample API 표본 배정 테스트 (POST)
    payload = {
        "region": "서울특별시|양천구",
        "sex": "여자",
        "age": "65~69",
        "cancer": "대장암",
        "n": 300,
        "seed": 42
    }
    response = client.post("/api/sample", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "campaign_id" in data
    assert "segment" in data
    assert "total_unscreened" in data
    assert "contact_n" in data
    assert "control_n" in data
    assert "assignment_method" in data
    assert "note" in data
    assert "download" in data
    
    assert data["contact_n"] == 300
    assert data["control_n"] == data["total_unscreened"] - 300
    assert data["segment"]["region"] == "서울특별시|양천구"
    assert data["segment"]["sex"] == "여자"
    assert data["segment"]["age"] == "65~69"
    assert data["segment"]["cancer"] == "대장암"

def test_api_actions_determinism():
    url = "/api/actions?region=서울특별시|양천구&sex=여자&age=65~69&cancer=대장암&year=2024"
    responses = [client.get(url).json() for _ in range(10)]
    first_resp = responses[0]
    for r in responses[1:]:
        assert r == first_resp, "Actions 비결정성 발생!"

def test_api_records_flow():
    # 1. sample API로 새 캠페인 등록
    sample_payload = {
        "region": "서울특별시|양천구",
        "sex": "여자",
        "age": "65~69",
        "cancer": "대장암",
        "n": 300,
        "seed": 42
    }
    sample_res = client.post("/api/sample", json=sample_payload)
    assert sample_res.status_code == 200
    sample_data = sample_res.json()
    campaign_id = sample_data["campaign_id"]
    
    # 2. records GET API로 등록 여부 확인
    get_res = client.get("/api/records?region=서울특별시|양천구&year=2026")  # 오늘 날짜 연도는 2026년으로 생성됨
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert len(get_data["campaigns"]) > 0
    
    # 생성된 캠페인이 목록 최상단(id 역순)에 위치하는지 검증
    latest_campaign = get_data["campaigns"][0]
    assert latest_campaign["id"] == campaign_id
    assert latest_campaign["contact_n"] == 300
    
    # 3. records POST API로 성과 기록 업데이트
    update_payload = {
        "campaign_id": campaign_id,
        "contacted": 280,
        "reached": 200,
        "reasons": {
            "안내문_미수신": 30,
            "이유있음": 90,
            "비용우려": 50
        },
        "sms_sent": 300,
        "sms_date": "2026-08-18"
    }
    post_res = client.post("/api/records", json=update_payload)
    assert post_res.status_code == 200
    assert post_res.json() == {"status": "success", "campaign_id": campaign_id}
    
    # 4. 다시 GET하여 데이터 업데이트 성공 여부 확인
    get_res2 = client.get("/api/records?region=서울특별시|양천구&year=2026")
    assert get_res2.status_code == 200
    get_data2 = get_res2.json()
    updated_campaign = get_data2["campaigns"][0]
    assert updated_campaign["id"] == campaign_id
    assert updated_campaign["contacted"] == 280
    assert updated_campaign["reached"] == 200
    assert updated_campaign["reasons"]["안내문_미수신"] == 30
    assert updated_campaign["reasons"]["이유있음"] == 90
    assert updated_campaign["reasons"]["비용우려"] == 50
    assert updated_campaign["sms_sent"] == 300
    assert updated_campaign["sms_date"] == "2026-08-18"

def test_api_message_generation():
    # message API (LLM) 호출 및 응답 스키마 테스트
    payload = {
        "region": "서울특별시|양천구",
        "sex": "여자",
        "age": "65~69",
        "cancer": "대장암",
        "tone": "standard"
    }
    response = client.post("/api/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "text" in data
    assert "facts_used" in data
    assert "reflected" in data
    assert "warning" in data
    assert data["warning"] == "발신 기관명은 보건소입니다. 온코케어를 노출하지 않습니다."
    
    # facts_used 검증
    assert len(data["facts_used"]) > 0
    fact_labels = [f["label"] for f in data["facts_used"]]
    assert "검진 주기" in fact_labels
    assert "본인부담" in fact_labels

def test_api_report_generation():
    # 1. JSON 포맷 리포트 테스트
    payload_json = {
        "region": "서울특별시|양천구",
        "year": 2024,
        "format": "json"
    }
    response_json = client.post("/api/report", json=payload_json)
    assert response_json.status_code == 200
    data = response_json.json()
    assert "text" in data
    assert "sections" in data
    assert len(data["sections"]) == 4
    
    # 2. DOCX 포맷 리포트 테스트 (바이너리 스트림 파일 응답)
    payload_docx = {
        "region": "서울특별시|양천구",
        "year": 2024,
        "format": "docx"
    }
    response_docx = client.post("/api/report", json=payload_docx)
    assert response_docx.status_code == 200
    assert response_docx.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(response_docx.content) > 0

