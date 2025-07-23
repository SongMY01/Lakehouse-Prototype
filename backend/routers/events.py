# -*- coding: utf-8 -*-
# file: routers/events.py
# desc: FastAPI 라우터 — 클라이언트에서 이벤트를 수신해 Redis Stream에 저장
# author: minyoung.song
# created: 2025-07-23

import logging
from fastapi import APIRouter, Request
from services.stream_writer import write_to_stream

logger = logging.getLogger(__name__)

# /api/events 엔드포인트용 라우터
router = APIRouter()

@router.post("")
async def receive_event(request: Request):
    """
    클라이언트로부터 이벤트를 수신해 Redis Stream에 저장하는 핸들러
    """
    # 이벤트 수신 로그
    logger.debug("요청 수신: /api/events")
    
    # 요청 본문을 JSON으로 파싱
    data = await request.json()
    logger.debug(f"요청 데이터 파싱 완료: {data}")
    
    # Redis Stream에 이벤트 쓰기
    result = await write_to_stream(data)
    logger.debug(f"Redis에 이벤트 저장 완료: {result}")
    
    return result