import os
import logging
from config.redis import r

logger = logging.getLogger(__name__)


MAX_STREAM_LENGTH = 10000

async def write_to_stream(data: dict):
    # event_type이 없으면 "unknown"으로 처리
    event_type = data.get("event_type", "unknown")

    # Redis가 허용하는 타입으로 변환 (모든 값을 str로)
    data_str = {k: str(v) for k, v in data.items()}

    # Stream 이름 결정
    stream_name = f"{event_type}_events"

    logger.debug(f"이벤트 수신: {event_type}, Stream: {stream_name}, Data: {data_str}")

    r.xadd(
        stream_name,
        data_str, # type: ignore
        maxlen=MAX_STREAM_LENGTH,
        approximate=True
    )

    logger.debug(f"이벤트가 Redis Stream '{stream_name}'에 기록됨")

    return {
        "status": "queued",
        "event_type": event_type,
        "stream": stream_name,
        "received": data
    }