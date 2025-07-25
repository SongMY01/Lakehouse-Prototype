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
from typing import Optional, List, Tuple
from pydantic import BaseModel

from pyiceberg.catalog import load_catalog
from config.rest import catalog, NAMESPACE_NAME, CATALOG_NAME


# 로깅 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# MinIO 연결 확인
def check_minio_connection():
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

# ---------------------------- SCHEMAS ----------------------------

class ClickEvent(BaseModel):
    altKey: Optional[bool] = False
    ctrlKey: Optional[bool] = False
    metaKey: Optional[bool] = False
    shiftKey: Optional[bool] = False
    timestamp: int
    type: str
    event_type: str = "click"
    button: Optional[int]
    buttons: Optional[int]
    clientX: Optional[int]
    clientY: Optional[int]
    pageX: Optional[int]
    pageY: Optional[int]
    screenX: Optional[int]
    screenY: Optional[int]
    relatedTarget: Optional[str]

def click_arrow_fields() -> List[Tuple[str, pa.DataType]]:
    return [
        ("altKey", pa.bool_()),
        ("ctrlKey", pa.bool_()),
        ("metaKey", pa.bool_()),
        ("shiftKey", pa.bool_()),
        ("button", pa.int32()),
        ("buttons", pa.int32()),
        ("clientX", pa.int32()),
        ("clientY", pa.int32()),
        ("pageX", pa.int32()),
        ("pageY", pa.int32()),
        ("screenX", pa.int32()),
        ("screenY", pa.int32()),
        ("relatedTarget", pa.string()),
        ("timestamp", pa.timestamp("ms")),
        ("type", pa.string()),
    ]

class KeydownEvent(BaseModel):
    altKey: Optional[bool] = False
    ctrlKey: Optional[bool] = False
    metaKey: Optional[bool] = False
    shiftKey: Optional[bool] = False
    timestamp: int
    type: str
    event_type: str = "keydown"
    key: str
    code: str

def keydown_arrow_fields() -> List[Tuple[str, pa.DataType]]:
    return [
        ("altKey", pa.bool_()),
        ("ctrlKey", pa.bool_()),
        ("metaKey", pa.bool_()),
        ("shiftKey", pa.bool_()),
        ("key", pa.string()),
        ("code", pa.string()),
        ("timestamp", pa.timestamp("ms")),
        ("type", pa.string()),
    ]

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
    try:
        r.xgroup_create(stream_name, GROUP_NAME, id='0', mkstream=True)
        logger.info(f"✅ 어플 구도 생성: {stream_name}:{GROUP_NAME}")
    except Exception as e:
        if "BUSYGROUP" in str(e):
            logger.info(f"✅ 어플 구도 기존: {stream_name}:{GROUP_NAME}")
        else:
            logger.error(f"🚨 어플 구도 생성 실패: {stream_name}: {e}")

def process_stream(stream_name):
    logger.info(f"🚀 스트림 소비 시작: {stream_name}")
    ensure_consumer_group(stream_name)
    event_type = stream_name.replace("_events", "")      
    table = catalog.load_table(f"{NAMESPACE_NAME}.{event_type}_events")
    schema_fields = SCHEMAS[event_type]

    while True:
        try:
            resp = r.xreadgroup(GROUP_NAME, "consumer-1", {stream_name: ">"}, count=BATCH_SIZE, block=5000)
            if not resp:
                continue

            batch, ids = [], []
            for _, messages in resp:
                for msg_id, fields in messages:
                    record = convert_to_record(fields, schema_fields)
                    batch.append(record)
                    ids.append(msg_id)

            if batch:
                rb = create_record_batch(batch, schema_fields)
                table.append(pa.Table.from_batches([rb]))
                logger.info(f"📋 [{stream_name}] 배치 적재 완료: {len(batch)}개")
                r.xack(stream_name, GROUP_NAME, *ids)

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