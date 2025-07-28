# -*- coding: utf-8 -*-
# file: redis_to_iceberg.py
# desc: Redis Stream → Iceberg 적재 파이프라인 (모든 구성 포함)
# author: 송민영
# created: 2025-07-25

import os
import boto3
import time
import logging
import threading
import glob
import importlib
import redis
import pyarrow as pa
from schemas.click_event import click_arrow_fields
from schemas.keydown_event import keydown_arrow_fields

from config.iceberg import catalog, NAMESPACE_NAME


# 로깅 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# MinIO 연결 확인
def check_minio_connection():
    """
    MinIO 연결 상태를 확인하고 버킷 목록을 로그로 출력합니다.

    Returns:
        None
    """
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=os.getenv("CATALOG_S3_ENDPOINT", "http://minio:9000"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        buckets = s3.list_buckets()
        logger.info(f"✅ MinIO 연결 성공: {[b['Name'] for b in buckets.get('Buckets', [])]}")
    except Exception as e:
        logger.error(f"🚨 MinIO 연결 실패: {e}")

check_minio_connection()

# Redis 연결
try:
    r = redis.Redis(host='sv_redis', port=6379, decode_responses=True)
    r.ping()
    logger.info("✅ Redis 연결 성공")
except Exception as e:
    logger.error(f"🚨 Redis 연결 실패: {e}")

# 공통 상수
GROUP_NAME = "worker-group"
BATCH_SIZE = 100
# ---------------------------- SCHEMA AUTO-LOADER ----------------------------

SCHEMAS = {}
schema_funcs = {
    "click": click_arrow_fields,
    "keydown": keydown_arrow_fields
}

for event_type, func in schema_funcs.items():
    SCHEMAS[event_type] = func()

# ---------------------------- RECORD & STREAM 처리 ----------------------------

def convert_to_record(fields, schema_fields):
    """
    Redis에서 읽은 필드를 PyArrow 스키마에 맞는 레코드(dict)로 변환합니다.

    Args:
        fields (dict): Redis에서 수신한 이벤트 필드
        schema_fields (list): PyArrow 스키마 필드 정의

    Returns:
        dict: 변환된 레코드
    """
    record = {}
    for k, typ in schema_fields:
        v = fields.get(k)
        if typ == pa.bool_():
            record[k] = True if v == "True" else False
        elif typ in [pa.int32(), pa.int64(), pa.timestamp("ms")]:
            try:
                record[k] = int(v) if v not in [None, ""] else 0
            except Exception:
                record[k] = 0
        else:
            record[k] = v if v is not None else ""
    return record

def create_record_batch(batch, schema_fields):
    """
    레코드 리스트를 PyArrow RecordBatch로 변환합니다.

    Args:
        batch (list): dict 형태의 레코드 리스트
        schema_fields (list): PyArrow 스키마 필드 정의

    Returns:
        pa.RecordBatch: 생성된 RecordBatch
    """
    columns, names = [], []
    for name, typ in schema_fields:
        col = []
        for r_ in batch:
            val = r_.get(name)
            if typ in [pa.int32(), pa.int64(), pa.timestamp("ms")]:
                val = 0 if val in [None, ""] else int(val)
            elif typ == pa.bool_():
                val = bool(val)
            elif typ == pa.string():
                val = val or ""
            col.append(val)
        columns.append(pa.array(col, type=typ))
        names.append(name)
    return pa.RecordBatch.from_arrays(columns, schema=pa.schema([
        pa.field(name, typ, nullable=False) for name, typ in zip(names, [typ for _, typ in schema_fields])
    ]))

def ensure_consumer_group(stream_name):
    """
    지정된 Redis Stream에 대해 Consumer Group이 존재하지 않으면 생성합니다.

    Args:
        stream_name (str): Redis Stream 이름

    Returns:
        None
    """
    try:
        r.xgroup_create(stream_name, GROUP_NAME, id='0', mkstream=True)
        logger.info(f"✅ 어플 구도 생성: {stream_name}:{GROUP_NAME}")
    except Exception as e:
        if "BUSYGROUP" in str(e):
            logger.info(f"✅ 어플 구도 기존: {stream_name}:{GROUP_NAME}")
        else:
            logger.error(f"🚨 어플 구도 생성 실패: {stream_name}: {e}")


def delete_from_stream(stream_name, ids):
    """
    Iceberg 적재 후 Redis Stream에서 처리된 메시지를 삭제합니다.

    Args:
        stream_name (str): Redis Stream 이름
        ids (list): 삭제할 메시지 ID 리스트

    Returns:
        None
    """
    time.sleep(5)  # 적재 안정성을 위해 대기
    for msg_id in ids:
        r.xdel(stream_name, msg_id)
    logger.info(f"🗑️ [{stream_name}] Stream에서 {len(ids)}건 삭제")


def process_stream(stream_name):
    """
    지정된 Redis Stream을 지속적으로 소비하여 배치 단위로 Iceberg에 적재합니다.

    Args:
        stream_name (str): Redis Stream 이름

    Returns:
        None
    """
    logger.info(f"🚀 스트림 소비 시작: {stream_name}")
    ensure_consumer_group(stream_name)

    batch, ids = [], []
    last_flush = time.time()
    event_type = stream_name.replace("_events", "")
    schema_fields = SCHEMAS[event_type]
    table = catalog.load_table(f"{NAMESPACE_NAME}.{event_type}_events")

    while True:
        try:
            resp = r.xreadgroup(GROUP_NAME, "consumer-1", {stream_name: ">"}, count=BATCH_SIZE, block=5000)
            now = time.time()

            if resp:
                for _, messages in resp:
                    for msg_id, fields in messages:
                        record = convert_to_record(fields, schema_fields)
                        batch.append(record)
                        ids.append(msg_id)

            if len(batch) >= BATCH_SIZE or (batch and now - last_flush >= 5):
                if batch:
                    rb = create_record_batch(batch, schema_fields)
                    table.append(pa.Table.from_batches([rb]))
                    logger.info(f"📋 [{stream_name}] 배치 적재 완료: {len(batch)}개")

                    # 메시지 삭제를 별도 스레드로 처리
                    threading.Thread(target=delete_from_stream, args=(stream_name, ids.copy())).start()
                    batch.clear()
                    ids.clear()
                    last_flush = now

        except Exception as e:
            logger.error(f"🚨 스트림 처리 실패: {stream_name}: {e}")
            time.sleep(2)

# ---------------------------- MAIN ----------------------------

if __name__ == "__main__":
    streams = [f"{k}_events" for k in SCHEMAS.keys()]
    threads = []
    for stream in streams:
        t = threading.Thread(target=process_stream, args=(stream,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()