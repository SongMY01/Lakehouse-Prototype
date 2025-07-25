import logging
from pyiceberg.catalog import load_catalog
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Iceberg + MinIO 설정
MINIO_ENDPOINT = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "test-bucket"

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
WAREHOUSE_META_PATH = BASE_DIR / "db/warehouse"

CATALOG_NAME = "user_catalog"
NAMESPACE_NAME = "user_events"

logger.info("Ensuring warehouse metadata directory exists at %s", WAREHOUSE_META_PATH)
os.makedirs(WAREHOUSE_META_PATH, exist_ok=True)

logger.info("Loading Iceberg catalog...")
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
logger.info("Iceberg catalog loaded successfully.")
