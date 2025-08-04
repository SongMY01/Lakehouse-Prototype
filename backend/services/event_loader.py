# -*- coding: utf-8 -*-
# file: event_loader.py
# desc: Kafka에서 mouse_events 토픽 메시지를 읽어 Iceberg에 적재하는 Consumer
# author: minyoung.song
# created: 2025-08-04

import os
import json
import time
import logging
import threading
import pyarrow as pa
from kafka import KafkaConsumer
from config.iceberg import catalog, NAMESPACE_NAME
from schemas.mouse_event import mouse_arrow_fields
from schemas.keydown_event import keydown_arrow_fields
from pyiceberg.exceptions import NoSuchTableError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

BATCH_SIZE = 100
CONSUMER_POLL_TIMEOUT_MS = 1000

SCHEMAS = {
    "mouse": mouse_arrow_fields(),
    "keydown": keydown_arrow_fields(),
}

def convert_to_record(msg_dict, schema_fields):
    record = {}
    for k, typ in schema_fields:
        v = msg_dict.get(k)
        # ✅ 중첩 구조 JSON을 문자열로 변환
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)

        if typ == pa.bool_():
            record[k] = bool(v)
        elif typ in [pa.int32(), pa.int64(), pa.timestamp("ms")]:
            try:
                record[k] = int(v) if v not in [None, ""] else 0
            except Exception:
                record[k] = 0
        elif typ == pa.float64():
            try:
                record[k] = float(v) if v not in [None, ""] else 0.0
            except Exception:
                record[k] = 0.0
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

def consume_and_write(topic_name):
    event_type = topic_name.replace("_events", "")
    schema_fields = SCHEMAS[event_type]
    try:
        table = catalog.load_table(f"{NAMESPACE_NAME}.{event_type}_events")
    except NoSuchTableError:
        logger.warning(f"🧊 Iceberg 테이블이 아직 존재하지 않음: {event_type}_events → 건너뜀")
        return  # 이 토픽은 처리하지 않음

    consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers="sv_kafka:29092",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    logger.info(f"📥 Kafka 토픽 '{topic_name}' 소비 시작...")

    batch = []
    last_flush = time.time()

    try:
        while True:
            records = consumer.poll(timeout_ms=CONSUMER_POLL_TIMEOUT_MS)
            now = time.time()

            for tp, messages in records.items():
                for msg in messages:
                    record = convert_to_record(msg.value, schema_fields)
                    batch.append(record)

            if len(batch) >= BATCH_SIZE or (batch and now - last_flush >= 5):
                rb = create_record_batch(batch, schema_fields)
                table.append(pa.Table.from_batches([rb]))
                logger.info(f"📋 Kafka → Iceberg 적재 완료 [{topic_name}]: {len(batch)}건")
                batch.clear()
                last_flush = now

    except KeyboardInterrupt:
        logger.info(f"🛑 소비자 종료: {topic_name} (사용자 중단)")

    finally:
        consumer.close()

if __name__ == "__main__":
    topics = ["mouse_events", "keydown_events"]
    threads = []
    for topic in topics:
        t = threading.Thread(target=consume_and_write, args=(topic,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()