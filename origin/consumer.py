import redis
import pyarrow as pa
from pyiceberg.catalog import load_catalog
import time
import os
import threading

# 🔷 Redis 설정
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

GROUP_NAME = 'worker-group'
CONSUMER_NAME = 'worker-1'

# 🔷 Iceberg 설정
MINIO_ENDPOINT = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "user-events"
warehouse_meta_path = "/Users/minyoung.song/projects/bmp/workspace/my-project/warehouse"


CATALOG_NAME = "user_catalog"
NAMESPACE_NAME = "user_events"

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

BATCH_SIZE = 10
TIMEOUT_SEC = 5

# 🔷 이벤트별 스키마 정의
SCHEMAS = {
    "click": [
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
    ],
    "keydown": [
        ("altKey", pa.bool_()),
        ("ctrlKey", pa.bool_()),
        ("metaKey", pa.bool_()),
        ("shiftKey", pa.bool_()),
        ("key", pa.string()),
        ("code", pa.string()),
        ("timestamp", pa.timestamp("ms")),
        ("type", pa.string()),
    ]
}


def delete_from_stream(stream_name, ids):
    """10초 후에 Stream에서 메시지 삭제"""
    time.sleep(5)
    for msg_id in ids:
        r.xdel(stream_name, msg_id)
    print(f"🗑️ [{stream_name}] Stream에서 {len(ids)}건 삭제 완료")


def process_stream(stream_name):
    """하나의 Stream을 처리하는 컨슈머"""
    try:
        r.xgroup_create(stream_name, GROUP_NAME, id='0', mkstream=True)
        print(f"✅ 컨슈머 그룹 생성: {stream_name}:{GROUP_NAME}")
    except redis.exceptions.ResponseError as e: # type: ignore
        if "BUSYGROUP" in str(e):
            print(f"✅ 컨슈머 그룹 이미 존재: {stream_name}:{GROUP_NAME}")
        else:
            raise e

    batch = []
    processed_ids = []
    last_flush = time.time()

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
            for stream, messages in msgs: # type: ignore
                for msg_id, fields in messages:
                    event_type = stream_name.replace("_events", "")
                    table_name = f"{NAMESPACE_NAME}.{event_type}_events"

                    # 필드 파싱
                    if event_type == "click":
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
                    elif event_type == "keydown":
                        record = {
                            "altKey": fields.get("altKey") == "True",
                            "ctrlKey": fields.get("ctrlKey") == "True",
                            "metaKey": fields.get("metaKey") == "True",
                            "shiftKey": fields.get("shiftKey") == "True",
                            "key": fields.get("key") or "",
                            "code": fields.get("code") or "",
                            "timestamp": int(fields.get("timestamp", 0)),
                            "type": fields.get("type") or ""
                        }
                    else:
                        print(f"🚨 알 수 없는 이벤트 타입: {event_type}")
                        r.xack(stream_name, GROUP_NAME, msg_id)
                        continue

                    batch.append(record)
                    processed_ids.append(msg_id)

                    r.xack(stream_name, GROUP_NAME, msg_id)

        # 배치 크기 or 타임아웃 도달 시점에 적재
        if len(batch) >= BATCH_SIZE or (batch and now - last_flush >= TIMEOUT_SEC):
            print(f"📋 [{stream_name}] 배치 적재 시작: {len(batch)}건")

            schema_fields = SCHEMAS[event_type]
            record_batch = pa.record_batch(
                [pa.array([r[name] for r in batch], type=typ) for name, typ in schema_fields],
                names=[name for name, _ in schema_fields]
            )

            try:
                table = catalog.load_table(table_name)
            except Exception as e:
                print(f"🚨 Iceberg 테이블 로드 실패: {table_name}\n{e}")
                batch.clear()
                processed_ids.clear()
                last_flush = now
                continue

            table_arrow = pa.Table.from_batches([record_batch])
            table.append(table_arrow)

            print(f"✅ [{stream_name}] Iceberg 적재 완료: {len(batch)}건")

            threading.Thread(
                target=delete_from_stream,
                args=(stream_name, processed_ids.copy(),)
            ).start()

            batch.clear()
            processed_ids.clear()
            last_flush = now


if __name__ == "__main__":
    try:
        streams = ['click_events', 'keydown_events']

        threads = []
        for stream in streams:
            t = threading.Thread(target=process_stream, args=(stream,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    except KeyboardInterrupt:
        print("\n👋 컨슈머를 정상적으로 종료합니다.")