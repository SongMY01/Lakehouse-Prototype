from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema, NestedField
from pyiceberg.types import StringType, LongType, TimestampType
import os

# MinIO 및 Iceberg 설정값
MINIO_ENDPOINT = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "test-bucket"
CATALOG_NAME = "user_catalog"  
REST_CATALOG_URI = "http://localhost:8181"

# 카탈로그 로드
catalog = load_catalog(
    CATALOG_NAME,
    **{
        "type": "rest",
        "uri": REST_CATALOG_URI,
        "warehouse": f"s3://{BUCKET_NAME}",
        "s3.endpoint": MINIO_ENDPOINT,
        "s3.access-key-id": ACCESS_KEY,
        "s3.secret-access-key": SECRET_KEY,
        "s3.region": "us-east-1",
    }
)

# 네임스페이스 생성
namespace_name = "test_namespace"
if (namespace_name,) not in catalog.list_namespaces():
    catalog.create_namespace(namespace_name)
    print(f"✅ 네임스페이스 생성됨: {namespace_name}")

# 스키마 정의 (✔️ NestedField 사용)
click_schema = Schema(
    NestedField(1, "id", LongType(), required=False),
    NestedField(2, "user_id", StringType(), required=False),
    NestedField(3, "event_type", StringType(), required=False),
    NestedField(4, "event_time", TimestampType(), required=False),
)

# 테이블 생성
table_name = f"{namespace_name}.click_events"
if table_name not in [".".join(t) for t in catalog.list_tables(namespace_name)]:
    catalog.create_table(table_name, schema=click_schema)
    print(f"✅ 테이블 생성: {table_name}")
else:
    print(f"✅ 테이블 이미 존재: {table_name}")

# 네임스페이스/테이블 목록 출력
print("\n📦 네임스페이스 목록:")
for ns in catalog.list_namespaces():
    print(" -", ns)

print("\n📋 테이블 목록:")
for ns in catalog.list_namespaces():
    tables = catalog.list_tables(ns)
    for table in tables:
        print(" -", ".".join(table))
