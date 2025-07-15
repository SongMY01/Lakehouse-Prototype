from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from pyiceberg.catalog import load_catalog
import pyarrow as pa
import pyarrow.compute as pc
import os
from datetime import datetime, timezone, timedelta


# FastAPI 애플리케이션 생성
app = FastAPI()

# CORS 허용 설정 (모든 오리진, 모든 메서드 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔷 MinIO 및 카탈로그 관련 설정
MINIO_ENDPOINT = "http://localhost:9000"           # MinIO 엔드포인트
ACCESS_KEY = "minioadmin"                          # MinIO 액세스 키
SECRET_KEY = "minioadmin"                          # MinIO 시크릿 키
BUCKET_NAME = "mouse-click"                          # 사용할 버킷 이름
warehouse_meta_path = "/Users/minyoung.song/projects/bmp/workspace/my-project/warehouse"  # 메타데이터 저장 경로

# 메타데이터 경로가 없으면 생성
os.makedirs(warehouse_meta_path, exist_ok=True)
# 설정
CATALOG_NAME = "mouse_catalog"                # 카탈로그 이름
NAMESPACE_NAME = "mouse_events"              # 네임스페이스 이름
TABLE_NAME = f"{NAMESPACE_NAME}.click_events"

# 🔷 Iceberg 카탈로그 로드 (sqlite + MinIO를 사용)
catalog = load_catalog(
    CATALOG_NAME,
    **{
        "type": "sql",   # sqlite를 사용
        "uri": f"sqlite:///{warehouse_meta_path}/pyiceberg_catalog.db",  # sqlite DB 경로
        "warehouse": f"s3://{BUCKET_NAME}",                              # 데이터 저장 위치
        "s3.endpoint": MINIO_ENDPOINT,                                  # MinIO 엔드포인트
        "s3.access-key-id": ACCESS_KEY,                                 # MinIO 액세스 키
        "s3.secret-access-key": SECRET_KEY,                             # MinIO 시크릿 키
        "s3.region": "us-east-1",                                       # 리전 (아무거나 OK)
    }
)

# 🔷 네임스페이스 확인 및 생성
if (NAMESPACE_NAME,) not in catalog.list_namespaces():
    catalog.create_namespace(NAMESPACE_NAME)
    print(f"✅ 네임스페이스 생성: {NAMESPACE_NAME}")
else:
    print(f"✅ 네임스페이스 존재함: {NAMESPACE_NAME}")

# 🔷 테이블 목록 확인
tables = [".".join(t) for t in catalog.list_tables(NAMESPACE_NAME)]
print(f"📋 현재 테이블 목록: {tables}")

# 테이블이 없으면 생성
if TABLE_NAME not in tables:
    # PyArrow로 테이블 스키마 정의
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

# 🔷 클릭 이벤트를 받는 API 엔드포인트 정의
@app.post("/api/click")
async def receive_click(request: Request):
    # 요청에서 JSON 데이터 읽기
    data = await request.json()
    print(f"📋 클릭 데이터: {data}")
    
    # 🔷 timestamp를 한국시간으로 변환
    KST = timezone(timedelta(hours=9))
    ts_utc_ms = data.get("timestamp", 0)  # 클라이언트에서 온 UTC ms
    ts_utc = datetime.fromtimestamp(ts_utc_ms / 1000, tz=timezone.utc)
    ts_kst = ts_utc.astimezone(KST)
    ts_kst_ms = int(ts_kst.timestamp() * 1000)  

    batch = pa.record_batch([
        pa.array([data.get("altKey", False)], type=pa.bool_()),
        pa.array([data.get("ctrlKey", False)], type=pa.bool_()),
        pa.array([data.get("metaKey", False)], type=pa.bool_()),
        pa.array([data.get("shiftKey", False)], type=pa.bool_()),
        pa.array([data.get("button", 0)], type=pa.int32()),
        pa.array([data.get("buttons", 0)], type=pa.int32()),
        pa.array([data.get("clientX", 0)], type=pa.int32()),
        pa.array([data.get("clientY", 0)], type=pa.int32()),
        pa.array([data.get("pageX", 0)], type=pa.int32()),
        pa.array([data.get("pageY", 0)], type=pa.int32()),
        pa.array([data.get("screenX", 0)], type=pa.int32()),
        pa.array([data.get("screenY", 0)], type=pa.int32()),
        pa.array([data.get("relatedTarget") or ""], type=pa.string()),  
        pa.array([ts_kst_ms], type=pa.timestamp("ms")), 
        pa.array([data.get("type") or ""], type=pa.string()),
    ], names=["altKey", "ctrlKey", "metaKey", "shiftKey", "button", "buttons", "clientX", "clientY", "pageX", "pageY", 
              "screenX", "screenY", "relatedTarget", "timestamp", "type"])

    # RecordBatch를 PyArrow Table로 변환
    table_arrow = pa.Table.from_batches([batch])

    # Iceberg 테이블에 데이터 추가
    table.append(table_arrow)

    # 성공 응답 반환
    return {"status": "ok", "received": data}
