from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from pyiceberg.catalog import load_catalog
import pyarrow as pa
import os
from datetime import datetime, timezone, timedelta
from queue import Queue
import threading

# FastAPI 애플리케이션 생성
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MinIO 및 카탈로그 관련 설정
MINIO_ENDPOINT = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "mouse-click"
warehouse_meta_path = "/Users/minyoung.song/projects/bmp/workspace/my-project/warehouse"

os.makedirs(warehouse_meta_path, exist_ok=True)

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

if (NAMESPACE_NAME,) not in catalog.list_namespaces():
    catalog.create_namespace(NAMESPACE_NAME)
    print(f"✅ 네임스페이스 생성: {NAMESPACE_NAME}")
else:
    print(f"✅ 네임스페이스 존재함: {NAMESPACE_NAME}")

tables = [".".join(t) for t in catalog.list_tables(NAMESPACE_NAME)]
print(f"📋 현재 테이블 목록: {tables}")

if TABLE_NAME not in tables:
    schema = pa.schema([
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
    ])
    table = catalog.create_table(TABLE_NAME, schema=schema)
    print(f"✅ 테이블 생성: {TABLE_NAME}")
else:
    table = catalog.load_table(TABLE_NAME)
    print(f"✅ 테이블 로드: {TABLE_NAME}")

# 🔷 큐 + 배치 관련 설정
q = Queue()
BATCH_SIZE = 10  # 원하는 건수로 설정

def flush_to_iceberg():
    """큐에 쌓인 데이터를 Iceberg에 배치 적재"""
    batch_list = []
    while not q.empty() and len(batch_list) < BATCH_SIZE:
        batch_list.append(q.get())

    if not batch_list:
        return

    print(f"📦 배치 적재: {len(batch_list)}건")

    # RecordBatch로 변환
    record_batch = pa.record_batch(
        [
            pa.array([row[0] for row in batch_list], type=pa.bool_()),
            pa.array([row[1] for row in batch_list], type=pa.bool_()),
            pa.array([row[2] for row in batch_list], type=pa.bool_()),
            pa.array([row[3] for row in batch_list], type=pa.bool_()),
            pa.array([row[4] for row in batch_list], type=pa.int32()),  # 🔷 int32로
            pa.array([row[5] for row in batch_list], type=pa.int32()),
            pa.array([row[6] for row in batch_list], type=pa.int32()),
            pa.array([row[7] for row in batch_list], type=pa.int32()),
            pa.array([row[8] for row in batch_list], type=pa.int32()),
            pa.array([row[9] for row in batch_list], type=pa.int32()),
            pa.array([row[10] for row in batch_list], type=pa.int32()),
            pa.array([row[11] for row in batch_list], type=pa.int32()),
            pa.array([row[12] for row in batch_list], type=pa.string()),
            pa.array([row[13] for row in batch_list], type=pa.timestamp("ms")),
            pa.array([row[14] for row in batch_list], type=pa.string()),
        ],
        names=[
            "altKey", "ctrlKey", "metaKey", "shiftKey", "button", "buttons",
            "clientX", "clientY", "pageX", "pageY", "screenX", "screenY",
            "relatedTarget", "timestamp", "type"
        ]
    )

    table_arrow = pa.Table.from_batches([record_batch])
    table.append(table_arrow)


@app.post("/api/click")
async def receive_click(request: Request):
    data = await request.json()

    ts_ms = data.get('timestamp')
    dt_utc = datetime.utcfromtimestamp(ts_ms / 1000)
    dt_kst = dt_utc + timedelta(hours=9)

    print(f"📅 클라이언트에서 받은 timestamp(ms): {ts_ms}")
    print(f"📅 UTC 시간: {dt_utc}")
    print(f"📅 KST 시간: {dt_kst}")

    
    print(f"📋 클릭 데이터: {data}")

    row = [
        data.get("altKey", False),
        data.get("ctrlKey", False),
        data.get("metaKey", False),
        data.get("shiftKey", False),
        data.get("button", 0),
        data.get("buttons", 0),
        data.get("clientX", 0),
        data.get("clientY", 0),
        data.get("pageX", 0),
        data.get("pageY", 0),
        data.get("screenX", 0),
        data.get("screenY", 0),
        data.get("relatedTarget") or "",
        int(dt_kst.timestamp() * 1000),
        data.get("type") or ""
    ]

    # 큐에 넣기
    q.put(row)

    # 건수 기반 배치 처리
    if q.qsize() >= BATCH_SIZE:
        threading.Thread(target=flush_to_iceberg).start()

    return {"status": "queued", "queued_size": q.qsize()}
