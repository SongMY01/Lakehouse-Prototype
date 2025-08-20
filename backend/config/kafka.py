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

# Kafka 브로커 주소들 (쉼표 구분 문자열 → 리스트 변환)
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "broker-1:19092,broker-2:19092,broker-3:19092")
KAFKA_BROKER_LIST = [host.strip() for host in KAFKA_BROKER.split(",")]

# KafkaProducer 객체 (싱글턴)
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER_LIST,
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
    return producer

def create_kafka_consumer(topic_name):
    return KafkaConsumer(
        topic_name,
        bootstrap_servers=KAFKA_BROKER_LIST,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )