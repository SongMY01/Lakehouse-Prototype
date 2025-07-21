from pyiceberg.catalog import load_catalog
import os

# Iceberg + MinIO 설정
MINIO_ENDPOINT = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "user-events"
WAREHOUSE_META_PATH = "./warehouse"


CATALOG_NAME = "user_catalog"
NAMESPACE_NAME = "user_events"

# 메타데이터 디렉토리 생성
os.makedirs(WAREHOUSE_META_PATH, exist_ok=True)

catalog = load_catalog(
    CATALOG_NAME,
    **{
        "type": "sql",
        "uri": f"sqlite:///{WAREHOUSE_META_PATH}/pyiceberg_catalog.db",
        "warehouse": f"s3://{BUCKET_NAME}",
        "s3.endpoint": MINIO_ENDPOINT,
        "s3.access-key-id": ACCESS_KEY,
        "s3.secret-access-key": SECRET_KEY,
        "s3.region": "us-east-1",
    }
)


