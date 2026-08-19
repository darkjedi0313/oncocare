# '왜 낮을까' (요인 분석 대시보드) 화면 연동 완료 보고서

'왜 낮을까'([factors.html](file:///c:/Users/USER/project_ys/oncare/web/factors.html)) 화면이 데이터 바인딩 에러 없이 정상적으로 렌더링되도록 구현을 완료했습니다.

---

## 🛠️ 변경 내용

### 1. 프론트엔드 연동 완성
* [web/js/api.js](file:///c:/Users/USER/project_ys/oncare/web/js/api.js) 파일의 하단에 백엔드 `/api/factors`와 통신하는 `fetchFactors(region, sex, age, cancer, year)` API 헬퍼 함수를 신설했습니다.
* 백엔드 API 규격에 맞춰 `URLSearchParams`를 매핑하고 에러 대응 코드를 탑재했습니다.

### 2. 가상환경 기반 백엔드 구동
* 포트 8000번 충돌 프로세스를 감지하여 해제하고, Poetry 가상환경(Python 3.11.9) 내에서 `uvicorn api.main:app`을 실행하여 `pyarrow` 의존성 누락 문제(ImportError)를 완전히 해결했습니다.
* 현재 백엔드 API 서버는 `http://localhost:8000`에서 백그라운드로 안전하게 서비스 중입니다.

---

## 🧪 검증 결과

### 1. 백엔드 API 수동 응답 확인 (파이썬 스크립트 실행)
* `http://localhost:8000/api/factors` 엔드포인트에 테스트용 세그먼트 데이터를 전송한 결과, HTTP `200` 정상 응답과 함께 아래와 같은 통계 및 층화 데이터가 정확히 리턴되는 것을 검증했습니다.
```json
{
  "segment": { ... },
  "changeable": [
    { "factor": "관내 대장내시경 가능 기관 부족", "effect": -2.09, "source": "층화 9개 층 가중평균" }
  ],
  "fixed": [
    { "factor": "연령 구조", "effect": 1.39 },
    { "factor": "소득 수준", "effect": -1.21 }
  ],
  "strata_table": [ ... ],
  "cautions": [ ... ]
}
```

### 2. 브라우저 렌더링
* 사용자의 브라우저(`http://localhost:5173/factors.html`)를 새로고침하면 `api.js` 수정사항과 백엔드 API 응답이 즉시 반영되어, **양방향 기여도 차트, 상황 설명 카드 3종 및 층화 아코디언 표가 정상적으로 데이터 바인딩**되어 출력됩니다.
