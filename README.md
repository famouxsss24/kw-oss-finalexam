# 일단막아 · DEFENSE FIRST

방위산업 실무자를 위한 보안 위협 대응책 추천 시스템입니다.
Streamlit 프론트에서 입력을 받고, FastAPI 백엔드가 위험도 계산과 추천 결과 생성을 담당합니다.

## 핵심 기능

- 부서 코드 기반 워크스페이스 로그인
- 사고대응 / 예방점검 2가지 진단 모드
- FastAPI `/recommend` 추천 API 호출
- 부서별 공유 케이스 목록
- 케이스 상태 업데이트
- 실무자별 대응 메모 기록
- Docker Compose 기반 front/back 분리 실행

## 데모 부서 코드

| 코드 | 부서 |
|---|---|
| `DAPA-OPS` | 방산보안대응팀 |
| `RND-LAB` | 무기체계연구소 |
| `SUPPLY-7` | 협력업체보안실 |

같은 부서 코드로 로그인한 실무자는 같은 케이스 목록과 메모를 공유합니다.

## 폴더 구조

```
.
├─ front/                # Streamlit 프론트엔드
│  ├─ app.py             #   진입점
│  ├─ views.py           #   화면(로그인/위저드/결과/공유케이스)
│  ├─ api.py             #   백엔드 호출
│  ├─ styles.py          #   CSS
│  └─ .streamlit/config.toml
├─ back/                 # FastAPI 백엔드
│  ├─ main.py            #   API 엔드포인트
│  ├─ logic.py           #   위험도 계산 / 대응책 생성
│  └─ storage.py         #   SQLite 저장소
├─ docker-compose.yml    # front/back 컨테이너 분리 실행
└─ .env.example
```

## Docker 실행

```bash
docker compose up --build
```

- Streamlit: <http://localhost:8501>
- FastAPI: <http://localhost:8000>
- FastAPI docs: <http://localhost:8000/docs>

## 로컬 실행

백엔드:

```bash
cd back
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

프론트:

```bash
cd front
pip install -r requirements.txt
streamlit run app.py
```

## API 흐름

```txt
부서 코드 로그인
  -> POST /auth/login

진단 입력
  -> Streamlit form
  -> POST /recommend
  -> FastAPI 규칙 기반 위험도 계산
  -> SQLite에 부서 케이스 저장
  -> Streamlit 결과 출력

공동 대응
  -> GET /departments/{department_id}/cases
  -> PATCH /cases/{case_id}/status
  -> POST /cases/{case_id}/notes
```

## 현재 구현 범위

현재 로그인은 과제 데모용 워크스페이스 로그인입니다. 비밀번호 인증이 아니라, 사전에 등록된 부서 코드를 입력하면 해당 부서의 공유 공간에 접속하는 방식입니다.

실제 서비스 수준으로 확장하려면 사용자 비밀번호 해시, JWT 세션, 부서 관리자 승인, 감사 로그를 추가하면 됩니다.
