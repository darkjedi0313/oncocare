# DEVELOPMENT.md — 개발 가이드

> 환경 설정부터 배포까지. 기능 명세는 `PRD.md`, 에이전트 규칙은 `AGENTS.md`.

---

## 1. 사전 준비

### 필요한 것

| 항목 | 버전 / 비고 |
|---|---|
| Python | 3.12 이상 |
| Git | |
| Gemini API 키 | W4(생성 기능)부터 필요. W1~W3은 불필요 |

### 원본 데이터 5종을 `data/raw/`에 배치

파일명을 변경하지 않는다. 파이프라인이 파일명으로 분기한다.

```
data/raw/
├── 국민건강보험공단_시군구별_성별_암검진_대상_및_수검인원_현황_20241231.xlsx
├── 국민건강보험공단_시군구별_검진기관_현황_20241231.xlsx
├── 국민연금공단_자격_시구신고_평균소득월액_20241231.csv
├── 국민건강보험공단_월별_시군구별_성별_연령별_직역별_건강보험_적용인구_20241231.csv
└── 국민건강보험공단_시군구별_국가건강검진_현황자료(일반검진_암검진)_20231231.zip
```

**공공데이터포털 다운로드 경로**

| 데이터 | 번호 |
|---|---|
| 시군구별 성별 암검진 대상 및 수검인원 현황 | 15126846 |
| 시군구별 국가건강검진 현황자료 | 15149732 |
| 국민연금공단 자격 시구신고 평균소득월액 | 3046077 |
| 시군구별 검진기관 현황 | 빅데이터실 제공 |
| 월별 시군구별 직역별 건강보험 적용인구 | 빅데이터실 제공 |

---

## 2. 설치

```bash
git clone <repo> oncocare && cd oncocare
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

`.env`에 키를 입력한다.

```
GEMINI_API_KEY=
```

### requirements.txt

```
pandas>=2.2
numpy>=1.26
scikit-learn>=1.5
openpyxl>=3.1
pyarrow>=16.0
fastapi>=0.115
uvicorn[standard]>=0.30
pydantic>=2.8
python-dotenv>=1.0
google-generativeai>=0.8
python-docx>=1.1
pytest>=8.0
```

**LightGBM은 설치하지 않는다.** 최종 모델이 scikit-learn 기본 포함 HistGradientBoosting이다.

---

## 3. 실행

### 3-1. 파이프라인 — 단계별로 실행하고 로그를 확인한다

```bash
python pipeline/run.py --stage s1      # 원천 로드
python pipeline/run.py --stage s2      # 표준화·키 생성
python pipeline/run.py --stage s3      # 결합
python pipeline/run.py --stage s4      # wide → long
python pipeline/run.py --stage s5      # 파생 피처
python pipeline/run.py --stage s6      # 시간 분할
python pipeline/run.py --stage all     # 전체
```

**한 번에 `--stage all`을 돌리지 말고 단계별로 확인한다.** 특히 S2·S3에서 매칭률을 봐야 한다.

### 검증 게이트 — 통과 못하면 다음 단계로 넘어가지 않는다

| 단계 | 확인할 것 | 기준 |
|---|---|---|
| S2 | 시도 종류 · 후행 공백 | **17개 · 0건** |
| S3 | 검진기관 매칭률 | **≥ 99%** |
| S3 | 소득 매칭률 | **≥ 85%** |
| S3 | 적용인구 매칭률 | **≥ 99%** |
| S4 | 세그먼트 행수 | **89,299 ± 100** |
| S4 | 수검률 범위 이탈 | **0건** |
| S5 | 피처 15개 결측 | **0건** |
| S6 | 학습·검증 타깃 평균 차이 | **≤ 1.0%p** |

### 3-2. 분석 산출물

```bash
python analysis/build_artifacts.py
```

출력 — `data/processed/` 하위 9종

```
expectation.parquet        기대치·잔차·회복 여지
similar_regions.json       시군구별 유사 20곳
similar_rates.parquet      유사 20곳 실제 평균·범위·SE
strata.parquet             9개 층 교차표
coefficients.json          선형회귀 계수 + 주의사항
national_avg.parquet       전국 세그먼트 평균
trend.parquet              연도별 추이
linkage_gap.parquet        일반검진 연계 격차
actions.json               개입 카드
```

### 기대 성능 — 미달 시 원인을 확인하고 기록한다

```
기대치 모델      R² ≥ 0.85 · MAE ≤ 4.5%p
유사 20곳       평균 표준오차 ≤ 2.0%p · 도농 일치율 ≥ 95%
```

### 3-3. API

```bash
uvicorn api.main:app --reload --port 8000
```

확인

```bash
curl "http://localhost:8000/api/summary?scope=sgg&region=서울특별시|양천구&year=2024"
open http://localhost:8000/docs      # Swagger UI
```

### 3-4. 프론트엔드

```bash
python -m http.server 5173 --directory web
open http://localhost:5173
```

**CORS** — 개발 중에는 `api/main.py`에서 `http://localhost:5173`을 허용한다. 운영에서는 정적 호스팅 도메인만 허용한다.

### 3-5. 테스트

```bash
pytest -q
pytest tests/test_no_llm_in_query.py -v
```

---

## 4. 알려진 데이터 결함 6건 — 대응 코드가 이미 있어야 한다

파이프라인 구축 시 발견한 결함이다. **처리 코드가 빠지면 조용히 잘못된 결과가 나온다.**

### ① 시도명 개편 미반영

동일 데이터 안에 「강원도」와 「강원특별자치도」가 혼재한다. 검진기관 파일은 구 명칭, 암검진 파일은 신 명칭을 쓴다.

```python
SIDO_MAP = {"강원도": "강원특별자치도", "전라북도": "전북특별자치도"}
```

### ② 시도명 후행 공백 — 가장 위험

검진기관 파일의 시도명에 후행 공백이 있다(`"경기도 "`). 육안으로 확인이 불가능하다.

```python
s = str(s).strip()
```

**미처리 시 매칭률 44%.** 처리 시 99.8%.

### ③ 연도별 스키마 불일치

암검진 xlsx의 2021년 시트만 컬럼 구성이 다르다. 암종별 분해 없이 전체 대상자만 제공한다.

**2021년을 제외한다.** 시차 변수 계산 시 2년 간격 구간이 생기는 것을 감안한다.

### ④ 행정구역 계층 불일치

암검진은 「부천시 소사구」 등 일반구 단위, 검진기관·소득은 「부천시」 단위다. 세종시는 시군구명이 공란인 경우가 있다.

```python
df["키_시"] = df["키"].str.replace(r"부천시 (소사|오정|원미)구", "부천시", regex=True)
df["키_시"] = df["키_시"].replace({"세종특별자치시|세종시": "세종특별자치시|"})
```

### ⑤ 시도 컬럼 결측 (붙임3)

대장암 판정 파일에 시도 컬럼이 없어 동명 시군구 7종이 충돌한다.

```
중구 6 · 동구 6 · 서구 5 · 남구 4 · 북구 4 · 강서구 2 · 고성군 2
```

**행 순서로 복원을 시도했으나 2018~2022년 시트에서 순서가 어긋났다.** 검증 없이 적용하면 「강원 거제시」 같은 존재하지 않는 조합이 생성된다. 동명 시군구 7종을 배제하는 보수적 처리를 선택했다.

### ⑥ 주석 행의 컬럼 위장

붙임2의 2019년 시트가 18열로 읽히나 마지막 열은 폐암이 아닌 주석 텍스트다. 그대로 처리하면 총계를 폐암으로 오독한다.

**연도별 컬럼 매핑을 분기한다.**

---

## 5. 트러블슈팅

| 증상 | 원인 | 조치 |
|---|---|---|
| 매칭률 44% 내외 | 후행 공백 미처리 | `.strip()` 확인 |
| 세그먼트 행수가 144,288 | 대상자 0 조합 미제외 | `대상자 > 0` 필터 확인 |
| 세그먼트 행수가 5만 이하 | 조인 키 불일치 | 시도명 표준화 확인 |
| R² 0.45 내외 | 선형회귀를 최종 모델로 사용 | HistGB로 교체 |
| R² 0.89 이상 | 전년수검률이 피처에 포함 | A안 15피처만 사용 |
| 폐암 수검률이 총계와 동일 | 2019년 컬럼 매핑 오류 | 연도별 분기 확인 |
| 조회 API 응답이 매번 다름 | LLM 혼입 | `test_no_llm_in_query.py` 실행 |
| xlsx 로드 실패 | openpyxl 미설치 또는 병합 헤더 | `skiprows`·`header` 확인 |
| csv 한글 깨짐 | 인코딩 | `encoding="cp949"` 시도 |

### 로그 확인 위치

```
pipeline/run.py       각 단계 후 검증 로그 stdout
analysis/build_artifacts.py   성능 지표 stdout
```

---

## 6. 배포

### 백엔드 (Railway)

```bash
# Procfile
web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

**환경변수** — `GEMINI_API_KEY`

**주의** — `data/processed/` 산출물을 배포에 포함해야 한다. 컨테이너에서 파이프라인을 돌리지 않는다. 로컬에서 생성한 parquet를 함께 올리거나 오브젝트 스토리지에서 받는다.

### 프론트엔드 (정적 호스팅)

`web/` 디렉터리를 그대로 배포한다. `js/api.js`의 `BASE_URL`을 운영 백엔드 주소로 바꾼다.

### 배포 후 확인

```
□ /docs 접속
□ /api/summary 응답
□ 화면 [0] 데이터 표시
□ /api/message 생성 동작 (API 키 확인)
□ CORS 오류 없음
```

---

## 7. 갱신 절차 — 다음 연도 데이터

```
1. data/raw/의 원본 파일을 새 연도판으로 교체 (파일명 유지)
2. python pipeline/run.py --stage all
3. 검증 로그 확인 — 행수·매칭률·범위
4. python analysis/build_artifacts.py
5. 성능 지표 확인 — R²·MAE가 크게 달라지면 원인 조사
6. data/processed/ 재배포
```

**전 과정에 수작업 개입이 없다.** 원본만 교체하면 재실행된다.

---

## 8. 일정 (12일 압축안)

원래 5주 계획을 12일로 압축한 우선순위다.

| 일 | 작업 | 산출물 |
|---|---|---|
| 1~3 | 파이프라인 S1~S6 | `segments.parquet` + 검증 로그 |
| 4~5 | 분석 산출물 9종 | parquet/json |
| 6~9 | 조회 API 6종 + 화면 [0][1][2] | 조회로 동작하는 웹 |
| 10~12 | 생성 API 2종 + 화면 [6][7] | LLM 기능 포함 |

### 축소 대상

| 화면 | 처리 |
|---|---|
| [3] 다른 지역은 | 화면만, 데이터 연결은 시간 남으면 |
| [4] 무엇을 할까 | 정적 카드로 대체 가능 |
| [5] 연락 명단 | 화면만 |
| [8] 실행 기록 | 화면만 · 발표에서 「구현 예정」으로 설명 |

**[6] 안내문 · [7] 보고서는 반드시 완성한다.** LLM 주력 기능이다.

---

## 9. 참조 문서

| 문서 | 내용 |
|---|---|
| `AGENTS.md` | AI 에이전트 지침 (도구 중립) |
| `CLAUDE.md` | Claude Code 전용 세부 규칙 |
| `PRD.md` | 화면 9종 · API 명세 · 수용 기준 |
| 3_데이터분석정의서_온코케어.docx | EDA 3건 · 모델링 3건 · 타깃 Y 정의 |
| 4_데이터파이프라인정의서_온코케어.docx | S1~S6 · 결함 6건 · 스키마 |
| 5_활용공공데이터_목록_온코케어.xlsx | 데이터 22종 · 번호 · 결합 키 |
| 3_온코케어_브랜드_가이드.pdf | 색상 · 톤앤매너 · 금지 표현 |
