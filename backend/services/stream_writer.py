# -*- coding: utf-8 -*-
# file: services/stream_writer.py
# desc: Redis Stream에 이벤트를 기록하는 서비스 함수
# author: minyoung.song
# created: 2025-07-23

import os
import logging
from config.redis import r

logger = logging.getLogger(__name__)

# Redis Stream의 최대 길이 설정 (이 이상은 오래된 항목부터 삭제)
MAX_STREAM_LENGTH = 10000

async def write_to_stream(data: dict):
    """
    클라이언트에서 전달된 이벤트 데이터를 Redis Stream에 기록합니다.

    Args:
        data (dict): 이벤트 데이터

    Returns:
        dict: 기록 결과 상태 및 메타 정보
    """
    # event_type이 없으면 "unknown"으로 처리
    event_type = data.get("event_type", "unknown")

    # Redis가 허용하는 타입으로 변환 (모든 값을 문자열로)
    data_str = {k: str(v) for k, v in data.items()}

    # Stream 이름 결정 (event_type 기반)
    stream_name = f"{event_type}_events"

    logger.debug(f"이벤트 수신: {event_type}, Stream: {stream_name}, Data: {data_str}")

    # Redis Stream에 이벤트 추가 (MAX_STREAM_LENGTH를 초과하면 자동으로 삭제)
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