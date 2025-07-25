from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema, NestedField
from pyiceberg.types import LongType, StringType
from pyiceberg.table import PartitionSpec

# REST Catalog 연결
catalog = load_catalog(
    name="rest",
    uri="http://localhost:8181",
    warehouse="s3://test-bucket/warehouse"
)

# 네임스페이스가 없을 때만 생성
if ("example",) not in catalog.list_namespaces():
    catalog.create_namespace("example")

# ✅ 스키마 정의 (필드 ID는 반드시 부여해야 함)
schema = Schema(
    NestedField(id=1, name="id", field_type=LongType(), required=True),
    NestedField(id=2, name="name", field_type=StringType(), required=True),
)
# ✅ 테이블 생성
table_name = ("example", "sample_table")
if table_name not in catalog.list_tables("example"):
    catalog.create_table(
        identifier=table_name,
        schema=schema,
    )

print("📦 테이블 생성 완료:", catalog.list_tables("example"))