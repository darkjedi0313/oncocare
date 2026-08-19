# 온코케어 (OncoCare) 대화형 AI '온코' 기능 구현 계획

본 계획서는 기존에 2차 개발 범위로 미루어 두었던 대화형 AI 어시스턴트 **「온코」** 기능을 구현하기 위한 구체적인 기술 아키텍처, 프롬프트 가이딩 전략, 그리고 화면 연동 방안을 제시합니다.

## User Review Required

> [!IMPORTANT]
> **1. 컨텍스트 기반 수치 검증 장치 (Hallucination 방지)**
> 온코 챗봇과의 대화 과정에서 LLM이 임의의 숫자(수검률, 순위 등)를 지어내어 사용자에게 잘못된 보건 행정 의사결정을 유도하는 것을 방지하기 위해, **현재 사용자가 바라보고 있는 화면의 데이터 요약 정보(JSON)를 백엔드에서 사전 확보하여 LLM의 System Prompt에 컨텍스트로 제공**합니다.
> 생성 완료 후, 답변 텍스트 내의 숫자가 컨텍스트 JSON에 실재하는 숫자인지 대조 검증하는 가드레일(`extract_numbers` 정규식 대조 및 최대 2회 재생성)을 백엔드에 탑재합니다.
> 
> **2. 개인정보 보호 준수**
> 온코와의 대화 로그 및 백엔드 파이프라인 전반에서 주민등록번호, 연락처, 실명 등의 **개인식별정보(PII)는 일절 수집/저장/LLM 전송을 수행하지 않으며**, 오직 세그먼트 통계치(연령대, 암종, 지역, 성별) 및 가상의 캠페인 성과 지표만을 통신 데이터로 활용합니다.

## Proposed Changes

### 1. 백엔드 (FastAPI)

---

#### [NEW] [chat.py](file:///c:/Users/USER/project_ys/oncare/api/routers/chat.py)
* **`/api/chat` POST 엔드포인트 개설**:
  * **Input**: `region` (지역), `sex` (성별), `age` (연령대), `cancer` (암종), `year` (연도) 등 현재 화면의 세그먼트 정보 + 사용자의 `message` 대화 히스토리 리스트.
  * **Processing**:
    1. 전달받은 세그먼트 메타 데이터를 기반으로 `expectation`, `similar_rates`, `strata` 데이터프레임에서 해당 조건의 요약 지표(수검률, 기대치, 유사평균, 전국평균, 층화 분석 격차, 권장 개입 전략 목록 등)를 백엔드 DB에서 정교하게 조회.
    2. 조회된 수치 정보 및 팩트 리스트를 마크다운 형태의 구조화된 컨텍스트로 변환.
    3. Gemini API 호출을 위한 System Prompt 설계:
       ```
       당신은 보건소 검진 담당자를 보조하는 AI 어시스턴트 '온코'입니다.
       오직 아래 제공된 컨텍스트(수검률 및 격차 정보) 내의 사실 및 수치만 인용하여 대답하십시오.
       임의의 수치나 지자체 순위를 꾸며내어 말하는 것은 엄격히 금지됩니다.
       답변 톤: 공손하고 전문적인 보건 행정 톤앤매너.
       ```
    4. `gemini-3.6-flash` 모델을 사용하여 답변을 생성하고, 응답 내 수치가 컨텍스트 수치 범위 내에 있는지 유효성 검증을 통과한 후 최종 답변 반환.

#### [MODIFY] [schemas.py](file:///c:/Users/USER/project_ys/oncare/api/schemas.py)
* **신규 대화 스키마 추가**:
  * `ChatMessage`: `role` ('user' | 'assistant'), `content` (텍스트) 모델.
  * `ChatRequest`: `segment` (FactorSegment), `year` (int), `history` (List[ChatMessage]) 모델.
  * `ChatResponse`: `reply` (str), `facts_used` (List[FactUsed]) 모델.

#### [MODIFY] [main.py](file:///c:/Users/USER/project_ys/oncare/api/main.py)
* 신설된 `chat_router`를 마운트하여 `/api/chat` 호출 활성화.

---

### 2. 프론트엔드 (HTML/CSS/JS)

---

#### [MODIFY] [api.js](file:///c:/Users/USER/project_ys/oncare/web/js/api.js)
* **`postChat(payload)` 비동기 AJAX 헬퍼 추가**:
  * `/api/chat` 엔드포인트로 현재 활성화된 세그먼트 정보와 대화 히스토리를 POST 전송하고 응답을 받는 헬퍼 작성.

#### [NEW] [chatbot.js](file:///c:/Users/USER/project_ys/oncare/web/js/chatbot.js)
* **공통 대화형 UI 모듈 개발**:
  * 모든 HTML 화면에 이식 가능한 슬라이드 아웃(Slide-out) 패널 형태의 챗봇 창 마크업 및 스타일 동적 바인딩.
  * **구성 요소**:
    * **헤더**: 온코 AI 타이틀, 대화창 닫기 버튼.
    * **대화창 바디**: 질문/답변 버블 리스트 및 로딩 스피너 애니메이션.
    * **하단 입력 영역**: 메시지 입력 폼, 전송 버튼.
    * **대화 추천 퀵 버튼**: "이 지역/세그먼트의 주요 부진 요인은 무엇인가요?", "권장하는 개입 전략과 근거 논문은 무엇인가요?" 등 1초 내 조회가 가능한 다이렉트 프롬프트 칩 배치.
  * **동적 컨텍스트 수집**: 전송 버튼 클릭 시, 각 HTML 화면의 전역 변수(`currentRegion`, `currentSex`, `currentAge`, `currentCancer`, `currentYear` 등)로부터 세그먼트 상황 메타데이터를 자동으로 추출하여 Payload에 동봉 전송.

#### [MODIFY] 모든 HTML 파일 (`index.html` ~ `history.html` 10개 파일)
* 기존 플로팅 버튼의 단순 경고창(`onclick="alert(...)"`) 호출을 제거하고, `js/chatbot.js` 컴포넌트 호출로 교체하여 버튼 클릭 시 화면 우측에서 자연스러운 온코 대화 패널이 활성화되도록 연동.

---

### 3. 테스트 및 검증

---

#### [NEW] [test_chat_api.py](file:///c:/Users/USER/project_ys/oncare/tests/test_chat_api.py)
* `/api/chat` API의 기본 통합 테스트 구축:
  * 세그먼트 컨텍스트 주입 및 올바른 JSON Response 포맷 반환 여부 검증.
  * 10회 반복 통신 시 수치 결정성 및 할루시네이션(임의 창조된 숫자) 배제 유효성 검증.

## Verification Plan

### Automated Tests
* 신규 테스트 케이스 실행:
  ```bash
  python -m pytest tests/test_chat_api.py -v
  ```
* 전체 28개 테스트의 무결한 합격(100% Passed) 보장.

### Manual Verification
* `monitoring.html` 또는 `strategy.html` 화면에서 온코 플로팅 버튼 클릭.
* 우측에서 대화 패널이 정상 슬라이딩되는지 확인.
* "이 세그먼트의 기대치 대비 격차를 알려줘" 라고 질문하여, 현재 표에 명시된 `격차` 수치(-11.3%p 등)를 소수점 첫째 자리까지 정확하게 답변에 인용하는지 확인.
