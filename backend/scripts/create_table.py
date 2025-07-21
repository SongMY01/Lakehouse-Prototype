import logging
import os
from dotenv import load_dotenv
from database.iceberg import catalog, NAMESPACE_NAME
from schemas.click_event import click_arrow_fields
from schemas.keydown_event import keydown_arrow_fields
import pyarrow as pa

# 🔷 .env 로드
load_dotenv()

# 🔷 로깅 설정
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

if (NAMESPACE_NAME,) not in catalog.list_namespaces():
    catalog.create_namespace(NAMESPACE_NAME)
    logger.info(f"✅ 네임스페이스 생성: {NAMESPACE_NAME}")
else:
    logger.info(f"✅ 네임스페이스 존재: {NAMESPACE_NAME}")

def create_table(table_name: str, schema_fields):
    full_table_name = f"{NAMESPACE_NAME}.{table_name}"
    existing = [".".join(t) for t in catalog.list_tables(NAMESPACE_NAME)]
    if full_table_name in existing:
        logger.info(f"✅ 테이블 이미 존재: {full_table_name}")
    else:
        schema = pa.schema(schema_fields)
        catalog.create_table(full_table_name, schema=schema)
        logger.info(f"✅ 테이블 생성: {full_table_name}")

create_table("click_events", click_arrow_fields())
create_table("keydown_events", keydown_arrow_fields())

logger.info("🎉 모든 테이블 생성 완료!")