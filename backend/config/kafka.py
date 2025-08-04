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

# Kafka Producer 생성 함수
def create_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: str(k).encode("utf-8") if k else None,
        retries=3
    )

# Kafka Consumer 생성 함수
def create_kafka_consumer(topic_name):
    return KafkaConsumer(
        topic_name,
        bootstrap_servers=KAFKA_BROKER,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
