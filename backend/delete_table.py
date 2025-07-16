from pyiceberg.catalog import load_catalog

# 🔷 MinIO 및 카탈로그 관련 설정
MINIO_ENDPOINT = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "mouse-click"
warehouse_meta_path = "/Users/minyoung.song/projects/bmp/workspace/my-project/warehouse"

CATALOG_NAME = "mouse_catalog"
NAMESPACE_NAME = "mouse_events"
TABLE_NAME = f"{NAMESPACE_NAME}.click_events"

# 🔷 Iceberg 카탈로그 로드
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

# 🔷 테이블 삭제
if (NAMESPACE_NAME,) not in catalog.list_namespaces():
    print(f"❌ 네임스페이스 {NAMESPACE_NAME} 없음")
else:
    tables = [".".join(t) for t in catalog.list_tables(NAMESPACE_NAME)]
    if TABLE_NAME in tables:
        catalog.drop_table(TABLE_NAME)
        print(f"✅ 테이블 삭제 완료: {TABLE_NAME}")
    else:
        print(f"❌ 테이블 {TABLE_NAME} 없음")
