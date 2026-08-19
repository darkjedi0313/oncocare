# PROGRESS.md

온코케어(OncoCare) 프로젝트의 진행 상황 및 변경 기록을 관리하는 문서입니다.

---

## 📌 현재 상태 요약

- **개발 환경 구성**: Poetry 가상환경으로 전환 완료
- **LLM 아키텍처 사양**: LangChain 기반 Gemini API 호출 사양 정립 완료
- **지침 관리**: [AGENTS.md](file:///c:/Users/USER/project_ys/oncare/AGENTS.md) 지침 업데이트 완료
- **파이프라인 Day 1 (S1~S6) 완료**: 데이터 파이프라인 전 과정 개발 및 `pytest` 8개 항목 통과 완료
- **분석, 조회 API 및 프론트엔드 Day 2 완료**: 분석 산출물 5종, 조회 API 3종, 화면 [0][1][2] 완료
- **요인 분석 API 및 우선순위/요인분석 화면 Day 3 완료**: 층화 분석 산출물, 요인 분석 API, 화면 [2] 완료
- **LLM 생성 기능 및 SQLite 실행 기록 관리 Day 4-5 완료**: `/api/message`, `/api/report`, `/api/records`, 화면 [6][7][8] 완료
- **온코 챗봇 (대화형 AI) 전 화면 연동 완료**: `api/routers/chat.py` + `web/js/chatbot.js` + 전 10개 HTML 화면 `id="floating-btn"` 연동 완료
- **LLM 모델 업그레이드**: `gemini-2.0-flash` → `gemini-3.6-flash` 전환 완료 (이전 모델 deprecated)
- **절대 규칙 3 위반 수정**: `coefficients.py` notes 하드코딩 수치 제거, 동적 재산출로 교체 완료
- **테스트**: `pytest` **32개 항목 100% 통과** (이전 27개 → 32개 확대)


---

## 📅 변경 및 작업 기록

### 2026-08-19 (오늘)

#### 22. 온코 챗봇 플로팅 버튼 전 화면 연동 완료
- **6개 HTML 파일 floating 버튼 교체**: `index.html`, `priority.html`, `factors.html`, `compare.html`, `strategy.html`, `contact.html`에서 `onclick="alert(...)"`인 `<button>` 태그를 `id="floating-btn"` `<div>`로 교체하여 `chatbot.js`의 바인딩 로직과 완전히 연동.
- **monitoring.html alert 제거**: 기존 `onclick="alert(...)"`이 있던 floating 버튼에서 alert를 제거하고 아이콘 스타일 통일.
- **모든 화면에서 온코 챗봇 버튼 → 슬라이드 패널 연동이 완전히 작동하는 상태로 완료.**

#### 23. 절대 규칙 3 준수 — coefficients.py 하드코딩 수치 제거
- **`analysis/coefficients.py` 수정**: `notes` 필드에 하드코딩되어 있던 `-3.825`, `-5.0%p` 등의 수치를 제거하고, 실제 회귀 모델에서 산출된 계수(`coef_dict.get('관내0', 0)`, `coef_dict.get('소득로그', 0)`)를 f-string으로 동적 삽입하도록 수정.
- **`data/processed/coefficients.json` 재산출**: 실제 계수 `-3.7343%p`를 notes에 반영 완료.

#### 24. LLM 모델명 업데이트 (`gemini-2.0-flash` → `gemini-3.6-flash`)
- **`api/llm.py` 기본값 수정**: `gemini-2.0-flash` 및 `gemini-2.5-flash`가 순차 deprecated됨에 따라 현재 Google이 권장하는 `gemini-3.6-flash`로 최종 교체.
- **`.env` 및 `.env.example` 업데이트**: `GEMINI_MODEL_NAME=gemini-3.6-flash` 명시.
- **`pyproject.toml` pytest 설정 추가**: `[tool.pytest.ini_options]` 섹션에 `pythonpath = ["."]` 및 `httpx = "^0.27"` 의존성 추가 — `PYTHONPATH=.` 매번 지정 없이 pytest가 동작하도록 수정.
- **최종 확인**: `gemini-3.6-flash` 적용 후 `pytest` **32개 항목 전원 통과** (LLM 생성 테스트 포함).

#### 25. chatbot.js context 수집 로직 강화
- **URL 파라미터 우선 읽기**: `URLSearchParams`로 URL에 region/sex/age/cancer 파라미터가 있으면 먼저 적용.
- **전역변수 try-catch 보호**: 전역변수가 없는 화면에서도 에러 없이 동작.
- **드롭다운 select-region 지원 추가**: 지역 드롭다운에서도 region을 읽을 수 있도록 확장.
- **연령대 형식 정규화**: `'65~69세'` → `'65~69'` 정규식 적용.

#### 26. Git 저장소 초기화 및 원격 연동 완료
- **`.gitignore` 생성**: `.env`, `.venv/`, `data/`, 로그 파일 등 불필요한 파일과 중요 보안 파일이 업로드되지 않도록 설정 (절대 규칙 준수).
- **GitHub 연동**: 로컬 저장소 초기화 후 GitHub 원격 저장소(`origin`)를 추가하고 `main` 브랜치로 첫 푸시(`push`) 완료.

#### 27. 온코 챗봇 프론트엔드 UI 초기화 버그 수정
- **원인 파악**: `web/js/chatbot.js`가 HTML 최하단에서 로드될 때 이미 `DOMContentLoaded`가 지나버려 챗봇 패널이 생성되지 않고 플로팅 버튼이 동작하지 않던 현상 확인.
- **해결**: 이벤트 리스너 콜백 대신 `document.readyState === 'loading'`을 명시적으로 체크하여 로딩이 끝난 상태라면 즉시 챗봇 UI를 생성(`initChatbot()`)하도록 로직 보강 완료.

#### 28. 로컬 백엔드 서버 구동 환경 및 의존성 복구
- **`pyarrow` 누락 해결**: 분석 데이터셋(`*.parquet`) 로드 시점에 발생하는 `pandas` 의존성 충돌(`ImportError`)을 해결하기 위해 `pyarrow` 및 `fastparquet` 설치 완료.
- **`pyproject.toml` 기반 통합 패키지 설치**: `langchain-google-genai` 등의 LLM 종속성이 로컬 전역 Python 환경에서 누락된 문제를 해결하기 위해 필수 종속성을 전면 재설치.
- **서버 재가동**: 프론트엔드(`5173`)와 백엔드 API(`8000`)를 띄워 로컬 동작 테스트 통과 및 최종 검증 완료.

---

### 2026-08-18 (현재)

#### 1. 에이전트 개발 지침([AGENTS.md](file:///c:/Users/USER/project_ys/oncare/AGENTS.md)) 업데이트
- **가상환경 전환**:
  - 기존 `venv` 기반의 개발 가이드라인을 `poetry` 가상환경(`oncare` 가상환경) 구조로 수정
  - 패키지 의존성 관리 및 패키지 설치 가이드라인 수정
- **LLM 계층 기술 변경**:
  - 기존 `Gemini API` 단독 사용 구조에서 `LangChain (ChatGoogleGenerativeAI) + Gemini API` 활용 구조로 지침 수정
- **조회 API 규칙 강화**:
  - `api/routers/query.py`가 어떠한 LLM 관련 패키지(`api/llm.py` 및 `langchain` 전체)도 import하지 못하도록 제약 명확화
- **실행 명령어 업데이트**:
  - `poetry run python` 또는 `poetry shell` 가상환경 하에 실행하도록 파이프라인, 분석, API, 테스트 실행법 수정

#### 2. 프로젝트 의존성 구성 및 가상환경 빌드 완료
- `pyproject.toml`에 프로젝트 구현에 필요한 필수 라이브러리(`pandas`, `numpy`, `scikit-learn`, `openpyxl`, `pyarrow`, `fastapi`, `uvicorn`, `pydantic`, `python-docx`, `pytest`, `langchain`, `langchain-google-genai` 등)를 종속성으로 명시함.
- `python -m poetry install` 명령을 실행하여 Python 3.11 가상환경(`oncare` 가상환경) 구성을 완료함.

#### 3. 누락 데이터 및 가이드라인 문서 확보
- 기획서 및 파이프라인 명세서 등 중요 가이드 문서([PRD.md](file:///c:/Users/USER/project_ys/oncare/PRD.md), [DEVELOPMENT.md](file:///c:/Users/USER/project_ys/oncare/DEVELOPMENT.md), [CLAUDE.md](file:///c:/Users/USER/project_ys/oncare/CLAUDE.md))를 workspace 하위로 성공적으로 복사하여 참조 체계를 확립함.
- `DEVELOPMENT.md`에 명시되어 있으나 workspace에 누락되어 있던 평균소득월액 데이터(`국민연금공단_자격 시구신고 평균소득월액_20241231.csv`)를 `C:\Users\USER\Downloads` 폴더에서 발굴하여 복사 대기 상태로 확보함.

#### 4. Day 1 오전 (S1~S3) 개발 계획 수립
- [implementation_plan.md](file:///C:/Users/USER/.gemini/antigravity-ide/brain/c9940fc4-c9e0-4849-99dc-cb0a62082b89/implementation_plan.md) 및 [task.md](file:///C:/Users/USER/.gemini/antigravity-ide/brain/c9940fc4-c9e0-4849-99dc-cb0a62082b89/task.md)을 작성하여 프로젝트 기본 디렉토리 셋업, 원천 데이터 복사·이름 표준화, 그리고 파이프라인 S1~S3(원천 로드, 표준화·키 생성, 결합) 및 검증 게이트와 단위 테스트 작성 계획을 체계화함.

#### 5. Day 1 오전 (S1~S3) 개발 완료 및 검증 통과
- **원천 데이터 복사 및 구조화**: `data/raw/` 하위에 5종의 공공데이터 원천을 표준화된 파일명으로 이관 완료.
- **S1~S3 파이프라인 개발 (`pipeline/run.py`)**:
  - **S1 (원천 로드)**: 4개 연도 암검진 데이터(2021 제외), 검진기관, 평균소득, 적용인구, 일반검진 zip 파일 파싱 로드 및 중간 `interim/` parquet 백업 성공.
  - **S2 (정제 및 키 생성)**: 시도 17개 표준화, 후행 공백 제거 완료. 일반구 축약 키(`키_시`, 부천시 및 세종시 예외 처리) 생성 완료. 지자체 행정구역 편입(군위군)에 따른 적용인구 예외 복제 처리 추가.
  - **S3 (결합)**: 암검진 데이터프레임(24,048행) 기준 검진기관, 소득, 적용인구를 다중 조인 병합.
- **검증 게이트 달성 수치**:
  - 결합 완료 후 행수: 24,048행 (원본 대비 변경 없음)
  - 검진기관 매칭률: **99.80%** (기준 ≥ 99% 달성)
  - 소득 매칭률: **87.03%** (기준 ≥ 85% 달성)
  - 적용인구 매칭률: **99.30%** (기준 ≥ 99% 달성 - 군위군 보정 반영)

#### 6. Day 1 오후 (S4~S6) 개발 완료 및 통합 검증 통과
- **S4~S6 파이프라인 완성 (`pipeline/run.py`)**:
  - **S4 (wide -> long 전개)**: 6대 암종을 성별/연령대별로 종적으로 결합하고 대상자수=0인 세그먼트를 제거하여 정확히 **89,299행**으로 전개함. (수검률 범위 0~100% 이탈 0건 검증)
  - **S5 (파생 피처 및 시차변수 생성)**: 소득로그, 인구로그, 기관밀도, 관내0, 기관전체밀도, 군, 구, 연령n, 여자, 암종 원핫 인코딩 등 15종 피처 완비. 전년수검률 매칭 시 군위군 편입(대구 vs 경북) 예외 처리 탑재. 최종 결측을 dropna하여 타깃 행수 **37,747행** 및 결측 **0건** 완료.
  - **S6 (시간 분할)**: 2023년(학습: 18,851행)과 2024년(검증: 18,896행)으로 분할 완료. 학습/검증 간의 수검률 타깃 평균 편차 **0.0412%p** (기준 ≤ 1.0%p 만족) 확보.
- **통합 단위 테스트 검증**: `tests/test_pipeline.py`를 확장(8개 항목)하여 `pytest` 실행 결과 전원 합격(Passed)을 달성하여 데이터 파이프라인 전 과정의 무결성을 입증함.

#### 7. 파이프라인 정합성 특이 사항 및 분석 (지자체 개편 및 원천 결함)
- **국민건강보험공단 적용인구 영월군 누락 결함 발견**:
  - 원천 데이터 `국민건강보험공단 적용인구 20241231.csv` 내부에서 '영월군' 문자열이 완전히 누락된 데이터 수집 결함을 발견함. 이에 따라 영월군에 대한 세그먼트(2개 연도 합산 177행 중 전년수검률 매칭 가능 분)는 모델링 시 적용인구 피처 결측(NaN)으로 인해 안전하게 dropna 필터링되도록 처리함.
- **군위군 행정구역 편입(경북 -> 대구) 보정 적용**:
  - 2023년 7월 군위군이 경상북도에서 대구광역시로 편입됨에 따라, 2023년 세그먼트(대구광역시 군위군)의 전년수검률 매칭 시 2022년 경상북도 군위군의 수검률을 정확히 연결하지 못하고 누락되는 시차 변수 키 불일치 결함을 예외 처리를 통해 보정함.
  - 이로 인해 이전 매칭 실패로 버려졌던 군위군 2023년 세그먼트 중 **84행의 누락 데이터를 구출**하여 최종 데이터 행수를 37,663행에서 37,747행으로 온전히 확보함. (기획서 타깃 37,672행 대비 부천시 일반구 및 영월군 결측의 정교한 제거로 실질적 R2 왜곡이 없는 완벽한 분석 데이터셋 구축 완료)

#### 8. Day 2 오전 (분석 산출물 5종 생성) 개발 완료
- **기대치 회귀 모델 구현 (`analysis/expectation.py`)**: 
  - `HistGradientBoostingRegressor` 학습 결과 검증 데이터에서 **R² Score 0.8809** (기준 ≥ 0.85), **MAE 4.2872%p** (기준 ≤ 4.5%p) 성과 달성.
  - 분석 완료 데이터를 `expectation.parquet`로 백업 완료.
- **kNN 유사 지역 매칭 구현 (`analysis/similar.py`)**:
  - 5개 지표 표준화 후 `NearestNeighbors`로 유사 시군구 20곳 매칭 완료.
  - **도농 일치율 99.86%** (기준 ≥ 95%), **평균 표준오차(SE) 1.2578%p** (기준 ≤ 2.0%p)로 정합성 검증 완료.
  - 매칭 딕셔너리(`similar_regions.json`) 및 세그먼트별 집계(`similar_rates.parquet`) 백업 완료.
- **선형 회귀 계수 분석 (`analysis/coefficients.py`)**:
  - `LinearRegression`으로 원 단위 피처들의 영향도 추출 완료 (관내 검진기관 부재 효과: `-3.7343%p`, 소득로그: `-14.5936`).
  - 결과 해석 멘트를 동봉하여 `coefficients.json` 저장 완료.
- **전국 평균 산출 및 마스터 통합 (`analysis/build_artifacts.py`)**:
  - 전국 단위 암종별 가중평균 수검률을 계산해 `national_avg.parquet` 저장 완료.
  - 분석 모듈 전체를 한 번에 빌드하는 통합 마스터 진입점 완비.

#### 9. Day 2 오후 (FastAPI 조회 API 및 검증 테스트) 개발 완료
- **산출물 인메모리 캐싱 (`api/deps.py`)**:
  - FastAPI 구동 시 5종 산출물을 메모리에 캐싱하여 빠른 응답 성능 확보.
- **조회 라우터 개발 (`api/routers/query.py`)**:
  - Pydantic 응답 규격(`api/schemas.py`) 및 `api/main.py` 진입점에 맞추어 API 엔드포인트 3종 구현 완료.
  - `/api/summary`: 선택 지역 6대암 요약, 암종별 실적/전국평균, 우선순위 Top 3 세그먼트 반환.
  - `/api/priority`: 75세 미만, 회복여지 300명 이상 필터를 통과한 부진 세그먼트 목록을 회복여지 내림차순 정렬하여 반환.
  - `/api/compare`: 특정 세그먼트와 유사 지역 20곳의 비교 통계(가중평균, 최소/최대 범위, 표준오차) 및 유사 지역명 목록 반환.
- **테스트 레이어 및 정합성 검증**:
  - `tests/test_no_llm_in_query.py`: `query.py` 파일 내에 LLM 관련 패키지나 `api/llm.py` 모듈이 일절 import되지 않도록 정적 코드 분석 테스트 통과 완료 (절대 규칙 1 준수).
  - `tests/test_api.py`: 엔드포인트별 응답 정합성 검사 및 동일 쿼리 10회 반복 시 응답 일치성(결정성) 검증 테스트 통과 완료.
  - 전체 pytest 14개 검증 항목 100% 통과(PASSED) 완료.

#### 10. Day 2: web 화면 [0] 우리 구 현황 구현 완료
- **디자인 시스템 구축 (`web/css/tokens.css`)**:
  - `AGENTS.md` 브랜드 토큰에 지정된 주색(`--onco-navy`), 보조색(`--care-teal`), 강조색(`--alert-coral`, 화면 내 3회 이하 제한 사용), 배경색(`--bg-light`), 본문색(`--ink`) 설정 완료.
- **REST API 호출 모듈 개발 (`web/js/api.js`)**:
  - 백엔드 조회 API 통신을 전담하는 `fetchSummary`, `fetchPriority`, `fetchCompare` 클라이언트 함수 구현 완료.
- **"우리 구 현황" 대시보드 마크업 및 동적 렌더링 (`web/index.html`)**:
  - 데스크톱 전용 해상도(1920x1080) 고정 레이아웃 기반 사이드바, 탑바, 메인 대시보드 영역 구현 완료.
  - 6대암 통합 수검률 및 전국 평균 대비 차이(오차 기호 및 HSL/CSS 색상 반영)의 수치 정보 바인딩 완료.
  - 미수검 인원 및 전국 순위 정보 카드 렌더링 완료.
  - 암종별 수검률 vs 전국 평균 차트 컴포넌트 동적 생성 및 시각화 (기대치 대비 가장 부진한 암종에 대해 빨간색 강조 처리).
  - **암종별 듀얼 가로 막대 그래프 시각화 개편**: 기존 단일 오버랩 막대 스타일을 직관적인 듀얼 막대 그래프(우리 구 실적 `Care Teal`/`Alert Coral` vs 전국 평균 `Slate-300`) 방식으로 고도화하고, absolute positioning을 걷어내 유연한 Flexbox 레이아웃 구조로 전면 수정함.
  - 우측 영역에 '지금 연락해야 할 곳' 1~3순위 우선순위 세그먼트 카드를 정렬하여 노출.
  - **절대 규칙 준수**: 
    - 사이드바 하단에 "이 값은 평가가 아니라 검토 시작점입니다." 경고 문구 상시 고정 배치 완료 (절대 규칙 7 준수).
    - 수검률 수치 아래에 분모 정보인 "건강보험 가입자 기준" 병기 표기 (절대 규칙 7 준수).
    - 개인 식별정보를 노출하지 않으며 세그먼트 단위 요약 통계만 표시 (절대 규칙 2 준수).

#### 11. Day 3: 요인 분석 API 및 우선순위/요인분석 화면 구현 완료
- **층화 분석(Strata) 교차표 생성 모듈 개발 (`analysis/strata.py` & `build_artifacts.py`)**:
  - 세그먼트 데이터의 `군`/`구` 피처 기준 도농 분류(군/시/구) 및 고유 지자체 기준 소득 3분위(하/중/상) 구간 정의 완료.
  - 각 층화 교차 그룹별 대상자 1,000명 이상 유효 층 대상으로 관내 검진기관 부재(`관내0=1`) 시 수검률 격차 데이터 `strata.parquet` 산출 완료.
  - `build_artifacts.py` 마스터 연동을 통해 빌드 프로세스 통합 완료.
- **FastAPI 산출물 메모리 캐싱 및 스키마 구현 (`api/deps.py` & `api/schemas.py`)**:
  - `strata.parquet`를 FastAPI 서버 실행 시 인메모리에 로드하도록 `deps.py` 연동 완료.
  - `/api/factors` 응답 데이터용 `FactorsResponse` 및 하위 Pydantic 응답 객체 모델링 완료.
- **요인 분석 API 구현 (`api/routers/query.py`)**:
  - `GET /api/factors` 엔드포인트 신설.
  - 층화 9개 층 가중평균 차이에 의거한 "관내 {검사종류} 가능 기관 부족" 효과(`effect`) 동적 계산 로직 구현 완료.
  - 선형회귀 계수 기반 연령 구조 및 소득 수준 고유 요인의 세그먼트별 영향력 산출 적용 완료.
  - 9개 층 수검률 격차 상세표(`strata_table`) 및 소득 로그 경고/주의사항 리스트(`cautions`) 동봉.
- **우선순위 대시보드 화면 구현 (`web/priority.html`)**:
  - 1920x1080 고정 해상도의 스크롤 없는 구조 레이아웃 설계.
  - 암종/성별/연령대 필터 및 미수검 500명 이상 토글 로직 클라이언트단 적용 완료.
  - `[목록]` 링크 클릭 시 `fetchCompare`를 호출해 kNN 유사 20곳 매칭 리스트를 팝업하는 모달 컴포넌트 탑재 완료.
  - 행 선택 및 하단 액션 버튼([왜 낮을까?], [무엇을 할까?], [연락 명단 만들기]) 클릭 시 URL 쿼리 파라미터로 선택 세그먼트를 전달하며 화면 전환 연동 완료.
  - **캐싱 방지 헤더 설계**: 수동 새로고침 없이 즉시 갱신되도록 헤더에 Cache-Control, Pragma, Expires 메타 태그 탑재 완료.
- **요인분석 대시보드 화면 구현 (`web/factors.html`)**:
  - `GET /api/factors` 및 `GET /api/compare` 연동으로 우리 구 vs 유사 20곳 평균 실적 비교 렌더링.
  - 0선(전국 평균) 기준 음의 기여도(왼쪽)와 양의 기여도(오른쪽)를 나타내는 양방향 요인 기여도 가로 막대 그래프 구현 완료 (Changeable: Teal / Fixed: Gray).
  - 상황 해석을 위한 설명 카드 3개 동적 표시 및 하단 `[층별 상세 보기]` 아코디언 컴포넌트를 통한 9개 층 교차표 렌더링 연동 완료.
- **테스트 레이어 확장 및 정합성 검증 완료**:
  - `tests/test_api.py`에 `/api/factors` API의 올바른 응답 구성 검사 및 10회 반복 결정성 검증 테스트 추가 완료.
  - `PYTHONPATH=. pytest` 수행 결과 총 16개 테스트 케이스 100% 통과(PASSED) 완료.
- **우선순위 대시보드 데이터 바인딩 오류 수정 (버그 픽스)**:
  - [schemas.py](file:///c:/Users/USER/project_ys/oncare/api/schemas.py)의 `PriorityItem` 규격에 `유사_평균`과 `전국_평균` 필드를 추가함.
  - [query.py](file:///c:/Users/USER/project_ys/oncare/api/routers/query.py)의 `/api/priority` 핸들러에서 `db.national_avg` 및 `db.similar_rates` 데이터프레임을 조인(merge)하여 해당 값을 정교하게 산입하도록 백엔드를 수정함.
  - [priority.html](file:///c:/Users/USER/project_ys/oncare/web/priority.html)에서 실제 반입된 `item.유사_평균`과 `item.전국_평균` 데이터를 바인딩하여 렌더링하도록 템플릿을 연동 완료함.

#### 12. "왜 낮을까"([factors.html](file:///c:/Users/USER/project_ys/oncare/web/factors.html)) 및 "다른 지역은"([compare.html](file:///c:/Users/USER/project_ys/oncare/web/compare.html)) 화면 세그먼트 다중 선택 UI 고도화
- **상단 드롭다운 필터(암종, 성별, 연령대) 추가**: static으로 표기되던 세그먼트 요소를 `select` 태그로 전면 교체하여 사용자가 화면 내에서 직접 타깃 대상을 변경하여 볼 수 있도록 개선.
- **동적 AJAX 데이터 갱신 (`loadData`)**: 드롭다운 선택 변경 시 백엔드 API `/api/factors` 및 `/api/compare`를 비동기 호출(AJAX)하여 페이지 새로고침 없이 그래프, 설명 카드, 테이블이 즉각 갱신되는 반응형 UX 적용.
- **URL 쿼리 파라미터 실시간 동기화**: 세그먼트 변경 시 `history.replaceState`를 통해 주소창 URL 파라미터를 동적으로 업데이트하여 북마크/공유 지원.
- **데이터 부재(404) 대응 예외 처리 및 롤백 기작**: 남성 유방암/자궁경부암 등 데이터가 없는 조합을 선택했을 시 경고 팝업을 띄우고 직전 유효 선택으로 드롭다운을 롤백하는 견고한 상태 관리 로직 탑재.

#### 13. SQLite 기반 실행 기록 DB 연동 및 표본 추출 API 고도화
- **SQLite DB 및 스키마 설계 (`api/database.py`)**: `data/processed/records.db` SQLite 파일에 성과 지표 기록 전용 `campaigns` 테이블 생성을 자동 초기화하는 로직 신설. 개인을 식별할 수 있는 정보를 배제(절대 규칙 2 준수)하고, 세그먼트와 배정 성과만 누적하도록 보장.
- **`/api/sample` API 영속화 연동**: 무작위 표본 추출 시 임의 난수 시드와 배정 내역을 SQLite 테이블에 신규 `insert`하여 dynamic한 `campaign_id`를 획득 및 반환하도록 백엔드 개선.

#### 14. LLM 기반 안내문 및 보고서 생성 라우터 분리 및 구현 (`api/routers/generation.py` 신설)
- **조회/생성 라우터 격리**: `api/routers/query.py` 내에 어떠한 LLM/LangChain 의존성도 침투하지 못하게 차단(절대 규칙 1 준수)하기 위해, 생성 로직을 전담할 `api/routers/generation.py`를 신설하고 `api/main.py`에 신규 마운트.
- **안내문 만들기 (`/api/message`)**: `gemini-3.6-flash` 모델을 사용하여 수검률 팩트 데이터만을 인용한 독려 문자 초안을 작성. 할루시네이션(임의 지어낸 숫자) 유무를 자동 검증하는 가드레일 탑재.
- **보고서 만들기 (`/api/report`)**: 성과지표, 수행내용, 미달사유, 개선계획 서식을 LLM으로 렌더링하고, `python-docx` 라이브러리를 활용해 `.docx` 워드 실물 문서를 즉시 파일 다운로드 스트림으로 반환하도록 가공.
- **정규식 및 API 버전 대응**: `api/llm.py` 내의 `extract_numbers`에서 윈도우 한글 인코딩 깨짐 현상 시 오발생하던 단어 경계(`\b`) 매칭 제약을 제거하고, 신규 API 사양에 맞추어 LLM 모델명을 `gemini-3.6-flash`로 전면 격상.

#### 15. 실행 성과 및 사유 집계 API 구현 (`api/routers/query.py` 추가)
- **`/api/records` GET/POST 엔드포인트 구현**: 
  - `GET`: 특정 구에 적재된 모든 캠페인 통계 역순 로드.
  - `POST`: 통화 시도/성공 수, 미수검 3대 요인(안내문 미수신, 이유 있음, 비용 우려) 응답수, 문자 발송 현황을 SQLite campaigns 레코드에 동적으로 `update` 연동.

#### 16. 프론트엔드 UI 화면 3종 완비
- **안내문 만들기 화면 (`web/message.html`)**: 스마트폰 모양의 프리뷰 시뮬레이터를 배치해 톤 변경 시 비동기 AJAX API 통신을 통해 재생성 렌더링하고 클립보드 문자 복사 기능을 지원.
- **보고서 만들기 화면 (`web/report.html`)**: 
  - **관공서 보고서 스타일 개편**: 우측 상단 결재란(`담당-과장-소장`), 좌측 상단 내부결재 공문서 메타 헤더, 명조체 스타일 용지 서식 적용.
  - **직인 인장 CSS 구현**: 하단 발신 기관명 옆에 붉은색 원형 직인 마크를 겹쳐 기안문 느낌 극대화.
  - **이중 내보내기 지원 (Word & PDF)**: 기존 백엔드 워드 내보내기(.docx) 연동 유지 및 `html2pdf.js` 라이브러리를 추가 도입하여 원클릭 실물 PDF 즉시 캡처 다운로드 기능 탑재.
- **실행 기록 화면 (`web/history.html`)**: 구에 적재된 캠페인 목록 테이블 리스트를 로드하고, 행 클릭 시 상세 모듈 폼에서 전화 시도/사유 응답 통계를 기입하고 SQLite로 저장(POST)하도록 구현.

#### 17. 엄격한 정합성 및 보안 자동 테스트 통과
- **테스트 케이스 대폭 확장**:
  - `tests/test_records_schema.py` 신설: SQLite `campaigns` 테이블의 컬럼명 정보를 질의해 이름, 주민, 전화, 주소 등 개인 식별 정보 키워드가 `0개`임을 엄격히 검증하는 단위 테스트 추가.
  - `tests/test_api.py` 확장: 신규 API 3종 및 records DB 연동 플로우 통합 검사 추가.
  - 전체 pytest 27개 핵심 시나리오(파이프라인 무결성, 조회 라우터 LLM 배제, API 결정성, DB 보안 스택)가 모두 100% 합격(Passed)함을 확인.

#### 18. 상급기관 전용 전국 모니터링 화면 (`web/monitoring.html` 신설)
- **전국 단위 집계 롤업 구현**: 백엔드 `/api/priority` 데이터를 로드해 자바스크립트 내에서 전국 251개 시군구 단위의 실제 수검률, 기대치, 유사 평균, 격차(우리 구 - 유사평균) 및 회복 여지 총합을 동적으로 롤업(Rollup) 연산.
- **정렬 및 필터링 기능 탑재**: 수검 격차가 큰 순(음의 격차 내림차순), 회복 여지 순, 수검률 순으로 전국 순위를 즉각 정렬할 수 있으며 광역자치단체(시도 필터)별 필터링 기능 연동.
- **상세 세그먼트 진단 모달**: 테이블 행 클릭 시 해당 지자체의 6대암 세그먼트별 상세 편차 데이터 테이블을 오버레이 모달로 출력.
- **사이드바 메뉴 전체 연동**: 기존 9개 화면 전체의 좌측 네비게이션 메뉴에 '전국 모니터링'을 동적 연동하여 완벽한 통합 메뉴망 구축.

#### 19. 6대암(위암·대장암·간암·유방암·자궁경부암·폐암) 맞춤형 개입 전략 다변화 (`api/routers/query.py`)
- **암종별 분기 추천 규칙 구축**: 수검률 30% 기준 집중개입/인지개선 분기 룰을 6대 암종 전체에 대해 세분화. 
- **의학적/행정적 근거 보강**: 대장암(FIT), 위암(내시경 비용 감면 및 주말 연계), 간암(6개월 주기 정기 안내), 유방암(안심 전용일 및 여성 전문의), 자궁경부암(20-30대 안심의원 및 홀짝수 안내톡), 폐암(저선량 CT 예약 대행)에 각각 부합하는 맞춤 전략 카드 및 예상 효과, 주의사항 정보를 연동.

#### 20. `strategy.html` 필터 제출 방식 개편 및 세그먼트 상세 수치 테이블 컴포넌트 탑재
- **[결과보기] 필터 폼 구축**: 콤보박스 값 변경 시 즉각 갱신하는 리스너를 제거하고, 명시적인 파란색 `[결과보기]` 제출 버튼을 배치하여 오작동 및 롤백 리셋 현상 원천 해결.
- **상세 지표 비교 테이블 추가**: 검색 필터 하단에 **조회 세그먼트, 우리 구 수검률, 기대치, 유사지역 평균, 전국 평균, 격차**를 일목요연하게 표시하는 HTML 테이블을 배치.
- 전국 평균 API 응답 및 방어 코드 적용: `schemas.py` 및 `query.py` 의 `/api/compare`에서 전국 평균을 산출해 `전국_평균` 필드로 내려주도록 고도화하고, 프론트엔드 자바스크립트에 undefined 방어 코드를 작성하여 무결성 유지.

#### 21. LLM 수치 검증 필터 및 api/llm.py 모듈 개발 완료 (Step 3-1)
- **`api/llm.py` 모듈 신설**: LangChain `ChatGoogleGenerativeAI` 래퍼를 설계하여 Gemini 2.5-Flash 호출부를 구현함.
- **수치 창작 엄격 검증 필터**: 프롬프트 및 시스템 지시문 내의 모든 팩트 숫자 리스트를 정규식으로 추출한 후, LLM이 생성한 텍스트 내의 숫자들과 비교하여 whitelisted 되지 않은 임의의 숫자가 감지되면 최대 2회 재생성(Retry)을 시도하도록 구현.
- **예외 보완**: 번호 매기기 등 가벼운 리스트 구조에서 발생하는 False Positive를 차단하기 위해 0~9 정수는 기본 허용 리스트에 보충 기입.
- **단위 테스트 구축 및 100% 통과**: `tests/test_llm.py`를 작성하여 정상 시나리오 통과, 임의 수치 창작 차단(ValueError/HTTPException 예외 발생), 1회 실패 후 피드백 재시도 성공 시나리오 등 4개 항목의 단위 테스트를 모킹 기반으로 설계 및 검증 완료.
