import os
import time
import logging
from datetime import datetime

import redis
import pyarrow as pa
from pyiceberg.catalog import load_catalog

# ──────────────────────────────
# 🔷 로깅 설정
# ──────────────────────────────
logging.basicConfig(
    filename='worker.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# ──────────────────────────────
# 🔷 Redis 설정
# ──────────────────────────────
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

STREAM_NAME = 'mouse_events'
GROUP_NAME = 'worker-group'
CONSUMER_NAME = 'worker-1'

# Consumer Group 생성 (이미 있으면 PASS)
try:
    r.xgroup_create(STREAM_NAME, GROUP_NAME, id='0', mkstream=True)
    print(f"✅ 컨슈머 그룹 생성: {GROUP_NAME}")
except redis.exceptions.ResponseError as e:
    if "BUSYGROUP" in str(e):
        print(f"✅ 컨슈머 그룹 이미 존재: {GROUP_NAME}")
    else:
        raise e

# ──────────────────────────────
# 🔷 Iceberg 설정
# ──────────────────────────────
MINIO_ENDPOINT = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "mouse-click"
warehouse_meta_path = "/Users/minyoung.song/projects/bmp/workspace/my-project/warehouse"

CATALOG_NAME = "mouse_catalog"
NAMESPACE_NAME = "mouse_events"
TABLE_NAME = f"{NAMESPACE_NAME}.click_events"

catalog = load_catalog(
    CATALOG_NAME,
    **{
        "type": "sql",
        "uri": f"sqlite:///{warehouse_meta_path}/pyiceberg_catalog.db",
        "warehouse": f"s3://{BUCKET_NAME}",
        "s3.endpoint": MINIO_ENDPOINT,
        "s3.access-key-id": ACCESS_KEY,
        "s3.secret-access-key": SECRET_KEY,
        "s3.region": "us-east-1",
    }
)

table = catalog.load_table(TABLE_NAME)

# ──────────────────────────────
# 🔷 배치 처리 설정
# ──────────────────────────────
BATCH_SIZE = 10
TIMEOUT_SEC = 60
block_timeout_ms = 5000  # Redis BLOCK 옵션 (ms)

batch = []
ack_ids = []
last_flush = time.time()

# ──────────────────────────────
# 🔷 무한 루프: 메시지 처리
# ──────────────────────────────
while True:
    # Redis Stream에서 메시지 읽기
    msgs = r.xreadgroup(
        groupname=GROUP_NAME,
        consumername=CONSUMER_NAME,
        streams={STREAM_NAME: '>'},
        count=BATCH_SIZE,
        block=block_timeout_ms
    )

    now = time.time()

    # 메시지를 읽은 경우
    if msgs:
        for stream, messages in msgs:
            for msg_id, fields in messages:
                record = {
                    "altKey": fields.get("altKey") == "True",
                    "ctrlKey": fields.get("ctrlKey") == "True",
                    "metaKey": fields.get("metaKey") == "True",
                    "shiftKey": fields.get("shiftKey") == "True",
                    "button": int(fields.get("button", 0)),
                    "buttons": int(fields.get("buttons", 0)),
                    "clientX": int(fields.get("clientX", 0)),
                    "clientY": int(fields.get("clientY", 0)),
                    "pageX": int(fields.get("pageX", 0)),
                    "pageY": int(fields.get("pageY", 0)),
                    "screenX": int(fields.get("screenX", 0)),
                    "screenY": int(fields.get("screenY", 0)),
                    "relatedTarget": fields.get("relatedTarget") or "",
                    "timestamp": int(fields.get("timestamp", 0)),
                    "type": fields.get("type") or ""
                }
                batch.append(record)
                ack_ids.append(msg_id)

    # 배치 크기 or 타임아웃 도달 시 처리
    if len(batch) >= BATCH_SIZE or (batch and now - last_flush >= TIMEOUT_SEC):
        logging.info(f"📋 배치 적재 시작: {len(batch)}건")

        try:
            # PyArrow RecordBatch 생성
            record_batch = pa.record_batch([
                pa.array([r["altKey"] for r in batch], type=pa.bool_()),
                pa.array([r["ctrlKey"] for r in batch], type=pa.bool_()),
                pa.array([r["metaKey"] for r in batch], type=pa.bool_()),
                pa.array([r["shiftKey"] for r in batch], type=pa.bool_()),
                pa.array([r["button"] for r in batch], type=pa.int32()),
                pa.array([r["buttons"] for r in batch], type=pa.int32()),
                pa.array([r["clientX"] for r in batch], type=pa.int32()),
                pa.array([r["clientY"] for r in batch], type=pa.int32()),
                pa.array([r["pageX"] for r in batch], type=pa.int32()),
                pa.array([r["pageY"] for r in batch], type=pa.int32()),
                pa.array([r["screenX"] for r in batch], type=pa.int32()),
                pa.array([r["screenY"] for r in batch], type=pa.int32()),
                pa.array([r["relatedTarget"] for r in batch], type=pa.string()),
                pa.array([r["timestamp"] for r in batch], type=pa.timestamp("ms")),
                pa.array([r["type"] for r in batch], type=pa.string()),
            ], names=[
                "altKey", "ctrlKey", "metaKey", "shiftKey", "button", "buttons",
                "clientX", "clientY", "pageX", "pageY", "screenX", "screenY",
                "relatedTarget", "timestamp", "type"
            ])

            table_arrow = pa.Table.from_batches([record_batch])
            table.append(table_arrow)

            # Iceberg 적재 후 ack
            for msg_id in ack_ids:
                r.xack(STREAM_NAME, GROUP_NAME, msg_id)

            logging.info(f"✅ Iceberg에 적재 완료 & ack: {len(batch)}건")

        except Exception as e:
            logging.error(f"❌ Iceberg 적재 실패: {e}")

        # 상태 초기화
        batch.clear()
        ack_ids.clear()
        last_flush = now
