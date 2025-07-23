# -*- coding: utf-8 -*-
# file: config/iceberg.py
# desc: Iceberg + MinIO 카탈로그를 초기화하고 로드하는 설정 모듈
# author: minyoung.song
# created: 2025-07-23

import os
import logging
from pathlib import Path

from pyiceberg.catalog import load_catalog

logger = logging.getLogger(__name__)

# Iceberg + MinIO 접속 설정
MINIO_ENDPOINT = "http://minio:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "user-events"

# backend/ 디렉토리 기준으로 Iceberg 메타데이터 저장 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
WAREHOUSE_META_PATH = BASE_DIR / "db/warehouse"

CATALOG_NAME = "user_catalog"
NAMESPACE_NAME = "user_events"

logger.info("Ensuring warehouse metadata directory exists at %s", WAREHOUSE_META_PATH)
# Iceberg 메타데이터 디렉토리 생성 (이미 존재하면 무시)
os.makedirs(WAREHOUSE_META_PATH, exist_ok=True)

logger.info("Loading Iceberg catalog...")

# Iceberg 카탈로그를 로드합니다.
# MinIO를 S3처럼 사용하고, 메타데이터는 sqlite에 저장.
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