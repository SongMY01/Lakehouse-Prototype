import redis
import pyarrow as pa
from pyiceberg.catalog import load_catalog
from datetime import datetime
import time
import os
import threading

# 🔷 Redis 설정
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

STREAM_NAME = 'mouse_events'
GROUP_NAME = 'worker-group'
CONSUMER_NAME = 'worker-1'

# 🔷 Iceberg 설정
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

# 🔷 Consumer Group 생성 (없을 때만)
try:
    r.xgroup_create(STREAM_NAME, GROUP_NAME, id='0', mkstream=True)
    print(f"✅ 컨슈머 그룹 생성: {GROUP_NAME}")
except redis.exceptions.ResponseError as e:
    if "BUSYGROUP" in str(e):
        print(f"✅ 컨슈머 그룹 이미 존재: {GROUP_NAME}")
    else:
        raise e

BATCH_SIZE = 10
TIMEOUT_SEC = 5

batch = []
processed_ids = []
last_flush = time.time()


def delete_from_stream(ids):
    """10초 후에 Stream에서 메시지 삭제"""
    time.sleep(5)
    for msg_id in ids:
        r.xdel(STREAM_NAME, msg_id)
    print(f"🗑️ Stream에서 {len(ids)}건 삭제 완료")


while True:
    msgs = r.xreadgroup(
        groupname=GROUP_NAME,
        consumername=CONSUMER_NAME,
        streams={STREAM_NAME: '>'},
        count=BATCH_SIZE,
        block=2000  # 최대 2초 대기
    )

    now = time.time()

    if msgs:
        for stream, messages in msgs:
            for msg_id, fields in messages:
                # Redis에서 가져온 데이터 파싱
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
                processed_ids.append(msg_id)

                # ack로 pending 목록에서 제거
                r.xack(STREAM_NAME, GROUP_NAME, msg_id)

    # 배치 크기 or 타임아웃 도달 시점에 적재
    if len(batch) >= BATCH_SIZE or (batch and now - last_flush >= TIMEOUT_SEC):
        print(f"📋 배치 적재 시작: {len(batch)}건")

        # Arrow RecordBatch 생성
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

        # Iceberg에 적재
        table_arrow = pa.Table.from_batches([record_batch])
        table.append(table_arrow)

        print(f"✅ Iceberg에 적재 완료: {len(batch)}건")

        # 10초 후에 Stream에서도 삭제 (백그라운드 스레드)
        threading.Thread(
            target=delete_from_stream,
            args=(processed_ids.copy(),)
        ).start()

        batch.clear()
        processed_ids.clear()
        last_flush = now
