from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import redis

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis 클라이언트 연결
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

STREAM_NAME = "mouse_events"

@app.post("/api/click")
async def receive_click(request: Request):
    data = await request.json()
    print(f"📋 수신된 이벤트: {data}")

    # Redis가 허용하는 타입으로 변환 (모든 값을 str로)
    data_str = {k: str(v) for k, v in data.items()}

    # Redis Streams에 추가
    r.xadd(STREAM_NAME, data_str, maxlen=10000, approximate=True)

    return {"status": "queued", "received": data}