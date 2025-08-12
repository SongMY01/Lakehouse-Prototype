# -*- coding: utf-8 -*-
# file: backend/main.py
# desc: FastAPI 애플리케이션 엔트리 포인트
# author: minyoung.song
# created: 2025-07-23

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import events

import os
import logging
from dotenv import load_dotenv

# 🔷 .env 로드 및 현재 경로 출력
load_dotenv()
# print(f"📄 Working Directory: {os.getcwd()}")

# 🔷 로깅 레벨 설정 (.env에 정의된 LOG_LEVEL 사용, 기본은 INFO)
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
os.environ["LOG_LEVEL"] = log_level  # FastAPI와 uvicorn에서 동일한 레벨 사용

# 🔷 Python 로깅 설정
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
logger.info(f"LOG_LEVEL 설정: {log_level}")

# 🔷 FastAPI 앱 생성
app = FastAPI(
    title="My Project API",
    description="FastAPI application entry point",
    version="1.0.0",
)

# 🔷 CORS 설정 (모든 origin 허용, 개발 환경용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔷 라우터 등록 (/api/events 엔드포인트에 events 라우터 연결)
app.include_router(events.router, prefix="/api/events", tags=["Events"])

@app.get("/")
async def root():
    """
    루트 엔드포인트
    """
    logger.debug("✅ 루트 엔드포인트 호출")
    return {"message": "Hello from FastAPI!"}

if __name__ == "__main__":
    import uvicorn

    # uvicorn 실행 (.env의 LOG_LEVEL과 동기화, reload 모드로 실행)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=log_level.lower(),  # uvicorn은 소문자
        access_log=False
    )