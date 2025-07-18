from pyiceberg.catalog import load_catalog
import pyarrow as pa
import os

MINIO_ENDPOINT = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "user-events"
warehouse_meta_path = "/Users/minyoung.song/projects/bmp/workspace/my-project/warehouse"  # 메타데이터 저장 경로

CATALOG_NAME = "user_catalog"
NAMESPACE_NAME = "user_events"

os.makedirs(warehouse_meta_path, exist_ok=True)

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
    print(f"✅ 네임스페이스 존재: {NAMESPACE_NAME}")

click_schema = pa.schema([
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

keyboard_schema = pa.schema([
    ("altKey", pa.bool_()),
    ("ctrlKey", pa.bool_()),
    ("metaKey", pa.bool_()),
    ("shiftKey", pa.bool_()),
    ("key", pa.string()),
    ("code", pa.string()),
    ("timestamp", pa.timestamp("ms")),
    ("type", pa.string()),
])

def create_table(table_name: str, schema: pa.Schema):
    full_table_name = f"{NAMESPACE_NAME}.{table_name}"
    existing_tables = [".".join(t) for t in catalog.list_tables(NAMESPACE_NAME)]

    if full_table_name in existing_tables:
        print(f"✅ 테이블 이미 존재: {full_table_name}")
    else:
        catalog.create_table(full_table_name, schema=schema)
        print(f"✅ 테이블 생성: {full_table_name}")

create_table("click_events", click_schema)
create_table("keydown_events", keyboard_schema)

print("🎉 모든 테이블 생성 완료!")
