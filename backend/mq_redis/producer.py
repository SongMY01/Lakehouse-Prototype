from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import redis

app = FastAPI()

# CORS 설정 — 모든 출처 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis 클라이언트 연결
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Redis Stream에 기록할 때 최대 길이
MAX_STREAM_LENGTH = 10000


@app.post("/api/event")
async def receive_event(request: Request):
    """
    유저 이벤트를 수신하고 Redis Stream에 저장
    event_type에 따라 Stream 이름을 결정
    """
    data = await request.json()
    print(f"📋 수신된 이벤트: {data}")

    # event_type이 없으면 "unknown"으로 처리
    event_type = data.get("event_type", "unknown")

    # Redis가 허용하는 타입으로 변환 (모든 값을 str로)
    data_str = {k: str(v) for k, v in data.items()}

    # Stream 이름 결정
    stream_name = f"{event_type}_events"

    # Redis Stream에 추가
    r.xadd(
        stream_name,
        data_str,
        maxlen=MAX_STREAM_LENGTH,
        approximate=True
    )

    return {
        "status": "queued",
        "event_type": event_type,
        "stream": stream_name,
        "received": data
    }
