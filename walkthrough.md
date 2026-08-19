# 통합 배포 (FastAPI + Vanilla JS) 작업 완료 보고서

FastAPI 백엔드가 프론트엔드 정적 파일(`web/` 폴더)까지 함께 제공하도록 구성하여 하나의 Railway 서비스로 전체 시스템을 배포할 수 있도록 설정을 완료했습니다.

## 변경 사항 요약

### 1. 백엔드 정적 파일 서빙 연동
* **파일**: [api/main.py](file:///c:/Users/USER/project_ys/oncare/api/main.py)
* **내용**: 
  - `fastapi.staticfiles.StaticFiles`를 사용하여 루트 경로 `/`로 정적 파일 폴더인 `web` 디렉터리를 서빙하도록 연동했습니다.
  - 기존 JSON 응답을 반환하던 테스트용 `/` 라우터를 제거하고, 모니터링 및 상태 확인용으로 `/api/health` 헬스체크 엔드포인트를 신설했습니다.

### 2. 프론트엔드 API 호출 주소 유연화
* **파일**: [web/js/api.js](file:///c:/Users/USER/project_ys/oncare/web/js/api.js)
* **내용**:
  - `const BASE_URL` 값을 `window.location.origin`으로 변경했습니다.
  - 이로써 로컬 개발 환경(`localhost:8000`)과 Railway 실서버 도메인 모두에서 별도의 코드 수정 없이 호스트 도메인을 자동으로 인식해 API를 요청하게 됩니다.

### 3. 빌드 필수 분석 산출물 Git 포함 설정
* **파일**: [.gitignore](file:///c:/Users/USER/project_ys/oncare/.gitignore)
* **내용**:
  - 기존에 `data/` 전체가 무시되어 Railway 빌드 시 데이터셋이 빠지던 문제를 해결했습니다.
  - `data/*`를 무시하되, 사전 계산 결과인 `!data/processed/` 폴더는 Git 추적 대상에 포함되도록 예외 처리했습니다. (raw 데이터는 여전히 차단됩니다.)

### 4. Railway 서버 구동 스크립트 작성
* **파일**: [Procfile](file:///c:/Users/USER/project_ys/oncare/Procfile)
* **내용**:
  - Railway 배포 시 자동으로 인식하여 uvicorn을 띄우도록 설정 파일을 생성했습니다.
  ```yaml
  web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
  ```

### 5. 테스트 스펙 업데이트 및 검증
* **파일**: [tests/test_api.py](file:///c:/Users/USER/project_ys/oncare/tests/test_api.py)
* **내용**:
  - 루트 경로 `/`의 응답이 JSON에서 HTML로 변경됨에 따라 `test_read_root` 검증 방식을 JSON 역직렬화 검사에서 HTML 콘텐츠 검사로 변경했습니다.
  - 개별 테스트 실행 결과 `test_read_root` 및 핵심 API 무결성 테스트가 정상 통과(`PASSED`)함을 확인했습니다.

---

## Railway 배포 시 후속 가이드

Railway 대시보드에서 배포를 진행할 때 다음 단계를 참고해 설정을 마무리해주시기 바랍니다.

1. **Variables (환경변수)**
   - Railway UI의 Variables 탭으로 이동하여 `GEMINI_API_KEY`를 추가합니다.
2. **Persistent Volume (SQLite DB 보존 - 선택사항)**
   - 캠페인 실행 기록 DB(`data/records.db`)를 보존하기 위해 Railway 서비스 내에 **Volume**을 생성한 후, 마운트 경로를 `/app/data` 혹은 프로젝트 데이터 경로에 맞춰 등록하면 배포 시마다 데이터베이스가 유실되는 현상을 막을 수 있습니다.
