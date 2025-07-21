# Backend

🎯 **Event Processing Backend**

클라이언트의 이벤트를 수신 → Redis에 저장 → Iceberg에 적재하는 백엔드 서비스입니다.  
FastAPI + Redis + Iceberg 기반으로 구성되었습니다.

---

## 📂 폴더 및 파일 구조

```
backend/
├── main.py                        # FastAPI 앱 진입점
├── README.md                      # 프로젝트 설명
├── pyproject.toml                 # 의존성 및 설정
├── routers/
│   ├── __init__.py
│   └── events.py                  # 이벤트 수신 라우터
├── services/
│   ├── __init__.py
│   ├── event_loader.py            # Redis → Iceberg 적재 프로세스
│   └── stream_writer.py           # Redis에 이벤트 쓰기
├── database/
│   ├── __init__.py
│   ├── redis.py                   # Redis 연결 설정
│   └── iceberg.py                 # Iceberg 설정
├── schemas/
│   ├── __init__.py
│   ├── click_event.py             # 마우스 클릭 이벤트 스키마
│   └── keydown_event.py           # 키보드 이벤트 스키마
├── scripts/
│   ├── __init__.py
│   └── create_tables.py          # Iceberg 테이블 생성 스크립트
├── warehouse/                     # Iceberg 메타데이터 및 데이터 저장소
    └── pyiceberg_catalog.db
```

---

## 🚀 실행 방법

### 📦 의존성 설치

[uv](https://github.com/astral-sh/uv) 사용 시:
```bash
uv sync
```

### 🖥 FastAPI 서버 실행

```bash
uv run python main.py
```

서버는 [http://localhost:8000](http://localhost:8000) 에서 실행됩니다.  
`/api/events` 엔드포인트로 이벤트 데이터를 POST 하면 됩니다.

### 📄 Redis → Iceberg 적재 프로세스 실행

```bash
uv run python -m services.event_loader
```

Redis 스트림의 데이터를 주기적으로 읽어 Iceberg 테이블에 저장합니다.

---

## 🔗 동작 흐름

```
[클라이언트]
   ↓ POST /api/events
[FastAPI (main.py)]
   ↓
[routers/events.py]
   ↓
[services/stream_writer.py]
   ↓
[Redis]
   ↓
[services/event_loader.py]
   ↓
[Iceberg]
```

1️⃣ 클라이언트가 `/api/events`에 이벤트 데이터를 전송합니다.  
2️⃣ FastAPI 라우터(`routers/events.py`)가 요청을 받아 Redis에 적재합니다.  
3️⃣ 별도로 실행되는 `services/event_loader.py`가 Redis 스트림을 읽고  
4️⃣ 데이터를 Iceberg에 적재합니다.

---
