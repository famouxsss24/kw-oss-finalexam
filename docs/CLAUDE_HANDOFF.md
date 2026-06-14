# Claude 전달용 작업 정리

## 현재 상황

프로젝트는 `PLAN.md`와 `docs/mockup.html`만 있던 초기 기획 상태에서, 과제 제출 구조에 맞춘 실제 실행 코드가 추가된 상태다.

이번 수정의 핵심은 기존 단순 추천 앱 기획에 **부서 코드 기반 워크스페이스 로그인**을 추가한 것이다. 방산 보안 실무자들이 개인 계정이 아니라 본인이 속한 부서 코드로 접속하고, 같은 부서의 실무자들이 동일한 사고 케이스를 공유하며 공동 대응하는 흐름을 만들었다.

## 추가된 폴더/파일

```txt
front/
  app.py
  Dockerfile
  requirements.txt
  .streamlit/config.toml

back/
  main.py
  logic.py
  storage.py
  Dockerfile
  requirements.txt

docker-compose.yml
.env.example
.gitignore
README.md
docs/CLAUDE_HANDOFF.md
```

## 기획 변경 포인트

### 기존 흐름

```txt
사용자 입력
  -> Streamlit
  -> FastAPI /recommend
  -> JSON 결과 반환
  -> Streamlit 결과 표시
```

### 수정 후 흐름

```txt
부서 코드 + 실무자 이름으로 로그인
  -> FastAPI /auth/login
  -> 부서 워크스페이스 세션 생성

진단 입력
  -> Streamlit form
  -> FastAPI /recommend
  -> 위험도 계산
  -> 추천 대응책 생성
  -> SQLite에 부서 케이스로 저장
  -> Streamlit 결과 표시

공동 대응
  -> 같은 부서 코드 사용자끼리 케이스 목록 공유
  -> 케이스 상태 변경
  -> 대응 메모 기록
```

## 데모용 부서 코드

백엔드 시작 시 SQLite에 아래 부서를 자동 등록한다.

| 부서 코드 | 부서명 |
|---|---|
| `DAPA-OPS` | 방산보안대응팀 |
| `RND-LAB` | 무기체계연구소 |
| `SUPPLY-7` | 협력업체보안실 |

## 백엔드 구현

### `back/main.py`

FastAPI 엔드포인트를 담당한다.

- `GET /health`
- `POST /auth/login`
- `POST /recommend`
- `GET /departments/{department_id}/cases`
- `PATCH /cases/{case_id}/status`
- `GET /cases/{case_id}/notes`
- `POST /cases/{case_id}/notes`

### `back/storage.py`

SQLite 저장소를 담당한다.

테이블:

- `departments`
- `operators`
- `cases`
- `case_notes`

역할:

- 부서 코드 검증
- 실무자 생성 또는 조회
- 부서별 케이스 저장/조회
- 케이스 상태 변경
- 케이스 메모 저장/조회

### `back/logic.py`

추천 로직을 담당한다.

현재는 규칙 기반 fallback 엔진이다.

점수 계산 기준:

- 자산 민감도
- 위협 유형
- 현재 보안수준
- 조직 환경
- 피해 상황 개수

반환 JSON에는 다음 필드가 포함된다.

```json
{
  "risk_score": 78,
  "risk_level": "HIGH",
  "threat_category": "APT 표적공격",
  "priority": "긴급",
  "summary": "...",
  "recommendations": [],
  "regulations": [],
  "engine": "rule-fallback"
}
```

## 프론트 구현

### `front/app.py`

Streamlit UI를 담당한다.

화면 구성:

1. 부서 워크스페이스 로그인
2. 새 진단
3. 부서 공유 케이스
4. 케이스 상태 업데이트
5. 대응 메모 작성/조회

로그인 입력:

- 부서 코드
- 실무자 이름

진단 모드:

- 사고대응
- 예방점검

중요한 점:

- 추천 계산은 Streamlit에서 하지 않는다.
- Streamlit은 입력 수집과 결과 표시만 담당한다.
- 위험도 계산과 케이스 저장은 FastAPI에서 수행한다.

## Docker 구성

`docker-compose.yml`은 front/back을 분리 실행한다.

- `front`: Streamlit, 포트 `8501`
- `back`: FastAPI, 포트 `8000`
- `defense_first_data` 볼륨: SQLite DB 보존

실행:

```bash
docker compose up --build
```

접속:

- Streamlit: `http://localhost:8501`
- FastAPI 문서: `http://localhost:8000/docs`

## 과제 어필 포인트

- 단순 추천 앱이 아니라 부서 단위 공동 대응 시스템처럼 보인다.
- Streamlit과 FastAPI의 실제 HTTP 통신이 명확하다.
- 추천 결과가 JSON으로 반환되고, 화면에 리포트 형태로 표시된다.
- SQLite를 사용해 케이스와 메모가 저장된다.
- Docker Compose로 front/back 컨테이너가 분리된다.
- EC2 데모에서 `docker ps`로 컨테이너 2개 실행을 보여주기 좋다.

## 아직 남은 개선 후보

현재는 과제 데모에 맞춘 최소 구현이다. 이후 Claude가 이어서 고도화한다면 아래를 추천한다.

- `ANTHROPIC_API_KEY`가 있을 때 Claude API로 추천 문장 고도화
- 부서 코드 외 비밀번호 또는 관리자 승인 추가
- 케이스 상세 화면 디자인 강화
- `docs/mockup.html`의 팔란티어풍 UI를 Streamlit CSS에 더 반영
- README에 EC2 배포 절차 이미지 또는 명령어 보강
- 테스트 코드 추가
