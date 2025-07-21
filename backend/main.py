from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import events

import os
import logging
from dotenv import load_dotenv

# 🔷 .env 로드 및 현재 경로 출력
load_dotenv()
# print(f"📄 Working Directory: {os.getcwd()}")
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
os.environ["LOG_LEVEL"] = log_level  # <- 추가

# 🔷 Python 로깅 설정
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
logger.info(f"LOG_LEVEL 설정: {log_level}")

app = FastAPI(
    title="My Project API",
    description="FastAPI application entry point",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(events.router, prefix="/api/events", tags=["Events"])

@app.get("/")
async def root():
    logger.debug("✅ 루트 엔드포인트 호출")
    return {"message": "Hello from FastAPI!"}

if __name__ == "__main__":
    import uvicorn

    # uvicorn 로그 레벨도 .env의 값으로 동기화
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=log_level.lower(),  # uvicorn은 소문자
    )