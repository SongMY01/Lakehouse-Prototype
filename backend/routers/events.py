import logging
from fastapi import APIRouter, Request
from services.stream_writer import write_to_stream

logger = logging.getLogger(__name__)

logger.debug("DEBUG 로그")   # .env가 INFO면 출력되지 않음
logger.info("INFO 로그")     # 출력

router = APIRouter()

@router.post("")
async def receive_event(request: Request):
    logger.debug("요청 수신: /api/events")
    data = await request.json()
    logger.debug(f"요청 데이터 파싱 완료: {data}")
    result = await write_to_stream(data)
    logger.debug(f"Redis에 이벤트 저장 완료: {result}")
    return result