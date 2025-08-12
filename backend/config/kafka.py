# -*- coding: utf-8 -*-
# file: config/kafka.py
# desc: Kafka 관련 설정 및 공통 객체
# author: minyoung.song
# created: 2025-08-04

import os
import json
import logging
from kafka import KafkaProducer, KafkaConsumer

logger = logging.getLogger(__name__)

# Kafka 브로커 주소
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "sv_kafka:29092")

# 프로그램 로드 시 1회 생성 → 재사용
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
    key_serializer=lambda k: str(k).encode("utf-8") if k else None,
    acks="all",
    compression_type="zstd",
    linger_ms=10,
    batch_size=256 * 1024,
    max_in_flight_requests_per_connection=5,
    retries=1000000,
    delivery_timeout_ms=120000,
    client_id="backend-producer-01",
    max_request_size=1048576
)
def get_kafka_producer():
    """싱글턴 KafkaProducer 반환"""
    return producer

# Kafka Consumer 생성 함수
def create_kafka_consumer(topic_name):
    return KafkaConsumer(
        topic_name,
        bootstrap_servers=KAFKA_BROKER,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
