# -*- coding: utf-8 -*-
# file: services/event_loader.py
# desc: Redis Stream에서 이벤트를 읽어 Iceberg에 적재하는 배치 로더
# author: minyoung.song
# created: 2025-07-23

import os
import glob
import threading
import time
import logging
import importlib
import redis
import pyarrow as pa

from config.redis import r
from config.iceberg import catalog, NAMESPACE_NAME

# 🔷 로깅 설정
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# 🔷 컨슈머 그룹 및 배치 설정
GROUP_NAME = "worker-group"
CONSUMER_NAME = "worker-1"
BATCH_SIZE = 10
TIMEOUT_SEC = 5

# 🔷 schemas 폴더의 스키마 모듈을 자동 로드해 SCHEMAS 구성
SCHEMAS = {}
schemas_path = os.path.join(os.path.dirname(__file__), "..", "schemas")
schema_files = glob.glob(os.path.join(schemas_path, "*_event.py"))

for f in schema_files:
    basename = os.path.basename(f).replace(".py", "")
    event_type = basename.replace("_event", "")
    module_name = f"schemas.{basename}"
    mod = importlib.import_module(module_name)
    arrow_func = getattr(mod, f"{event_type}_arrow_fields")
    SCHEMAS[event_type] = arrow_func()

def convert_to_record(fields, schema_fields):
    """
    Redis 메시지를 Iceberg 스키마에 맞는 레코드(dict)로 변환

    Args:
        fields (dict): Redis에서 읽은 데이터
        schema_fields (List[Tuple[str, pa.DataType]]): Iceberg 테이블 스키마

    Returns:
        dict: Iceberg에 적재 가능한 레코드
    """
    record = {}
    for k, typ in schema_fields:
        v = fields.get(k)
        # 타입에 맞게 안전하게 변환
        if typ == pa.bool_():
            record[k] = True if v == "True" else False
        elif typ == pa.int32():
            try:
                record[k] = int(v) if v not in [None, ""] else 0
            except (ValueError, TypeError):
                record[k] = 0
        elif typ == pa.timestamp("ms"):
            try:
                record[k] = int(v) if v not in [None, ""] else 0
            except (ValueError, TypeError):
                record[k] = 0
        else:
            record[k] = v if v is not None else ""
    return record

def create_record_batch(batch, schema_fields):
    """
    batch 데이터를 PyArrow RecordBatch로 생성

    Args:
        batch (List[dict]): 변환된 레코드 리스트
        schema_fields (List[Tuple[str, pa.DataType]]): Iceberg 테이블 스키마

    Returns:
        pyarrow.RecordBatch: Iceberg에 적재할 RecordBatch
    """
    columns, names = [], []
    for name, typ in schema_fields:
        col = []
        for r_ in batch:
            val = r_.get(name)
            if typ == pa.int32():
                if val in [None, ""]:
                    val = 0
                elif not isinstance(val, int):
                    try:
                        val = int(val)
                    except (ValueError, TypeError):
                        val = 0
            if typ == pa.bool_():
                val = bool(val) if val not in [None, ""] else False
            if typ == pa.string() and val is None:
                val = ""
            if typ == pa.timestamp("ms"):
                if val in [None, ""]:
                    val = 0
                elif not isinstance(val, int):
                    try:
                        val = int(val)
                    except (ValueError, TypeError):
                        val = 0
            col.append(val)
        columns.append(pa.array(col, type=typ))
        names.append(name)
    return pa.record_batch(columns, names=names)

def delete_from_stream(stream_name, ids):
    """
    Iceberg 적재 완료 후 Redis에서 메시지 삭제
    """
    time.sleep(5)  # 적재 안정성을 위해 대기
    for msg_id in ids:
        r.xdel(stream_name, msg_id)
    logger.info(f"🗑️ [{stream_name}] Stream에서 {len(ids)}건 삭제")


# --- 리팩토링: 컨슈머 그룹 생성, 메시지 처리, 배치 적재 함수화 ---

def ensure_consumer_group(stream_name):
    """
    지정한 Redis Stream에 컨슈머 그룹이 없으면 생성
    """
    try:
        r.xgroup_create(stream_name, GROUP_NAME, id='0', mkstream=True)
        logger.info(f"✅ 컨슈머 그룹 생성: {stream_name}:{GROUP_NAME}")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            logger.info(f"✅ 컨슈머 그룹 이미 존재: {stream_name}:{GROUP_NAME}")
        else:
            raise e

def process_messages(msgs, stream_name, batch, ids):
    """
    Redis 메시지를 읽어 배치에 추가하고 ack 처리
    """
    table_name = None
    schema_fields = None
    for _, messages in msgs:
        for msg_id, fields in messages:
            event_type = stream_name.replace("_events", "")
            table_name = f"{NAMESPACE_NAME}.{event_type}_events"
            schema_fields = SCHEMAS[event_type]

            record = convert_to_record(fields, schema_fields)
            batch.append(record)
            ids.append(msg_id)
            r.xack(stream_name, GROUP_NAME, msg_id)
    # 마지막 메시지에 필요한 메타데이터 반환
    if batch:
        return table_name, schema_fields
    return None, None

def write_batch_to_iceberg(batch, schema_fields, table_name, stream_name):
    """
    배치를 Iceberg에 적재하고 Redis 메시지를 삭제
    """
    logger.info(f"📋 [{stream_name}] 배치 적재 시작: {len(batch)}건")
    record_batch = create_record_batch(batch, schema_fields)
    try:
        table = catalog.load_table(table_name)
        table.append(pa.Table.from_batches([record_batch]))
        logger.info(f"✅ [{stream_name}] Iceberg 적재 완료: {len(batch)}건")
    except Exception as e:
        logger.error(f"🚨 Iceberg 테이블 로드 실패: {table_name}\n{e}")

def process_stream(stream_name):
    """
    지정된 Redis Stream에서 배치 단위로 읽어 Iceberg에 적재
    """
    ensure_consumer_group(stream_name)

    batch, ids = [], []
    last_flush = time.time()
    table_name, schema_fields = None, None

    while True:
        msgs = r.xreadgroup(
            groupname=GROUP_NAME,
            consumername=CONSUMER_NAME,
            streams={stream_name: '>'},
            count=BATCH_SIZE,
            block=2000
        )
        now = time.time()
        if msgs:
            table_name, schema_fields = process_messages(msgs, stream_name, batch, ids)

        if len(batch) >= BATCH_SIZE or (batch and now - last_flush >= TIMEOUT_SEC):
            if table_name and schema_fields:
                write_batch_to_iceberg(batch, schema_fields, table_name, stream_name)
            else:
                logger.warning(f"🚨 [{stream_name}] 배치 적재 정보 누락 (table_name or schema_fields 없음)")

            threading.Thread(
                target=delete_from_stream,
                args=(stream_name, ids.copy(),)
            ).start()
            batch.clear()
            ids.clear()
            last_flush = now

if __name__ == "__main__":
    # schemas 폴더의 *_event.py 파일을 기반으로 Stream 이름을 생성해 각 Stream을 독립 쓰레드에서 실행
    streams = [os.path.basename(f).replace("_event.py", "_events") for f in schema_files]
    threads = []
    for stream in streams:
        t = threading.Thread(target=process_stream, args=(stream,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()