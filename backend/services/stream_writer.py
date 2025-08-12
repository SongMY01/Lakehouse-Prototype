# -*- coding: utf-8 -*-
# file: services/stream_writer.py
# desc: Kafka에 이벤트를 기록하는 서비스 함수
# author: minyoung.song
# created: 2025-08-04

import logging
from config.kafka import get_kafka_producer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Kafka Producer 초기화
producer = get_kafka_producer()

async def write_to_stream(data: dict):
    """
    클라이언트에서 전달된 이벤트 데이터를 Kafka에 기록합니다.

    Args:
        data (dict): 이벤트 데이터

    Returns:
        dict: 기록 결과 상태 및 메타 정보
    """
    event_type = data.get("stream", "unknown")
    topic_name = f"{event_type}_events"

    # Kafka 전송
    producer.send(topic_name, key=None, value=data)

    logger.debug(f"이벤트가 Kafka 토픽 '{topic_name}'에 기록됨")

    return {
        "status": "queued",
        "type": event_type,
        "topic": topic_name,
        "received": data
    }