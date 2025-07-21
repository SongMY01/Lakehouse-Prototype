from database.iceberg import catalog, NAMESPACE_NAME
from schemas.click_event import click_arrow_fields
from schemas.keydown_event import keydown_arrow_fields
import pyarrow as pa

if (NAMESPACE_NAME,) not in catalog.list_namespaces():
    catalog.create_namespace(NAMESPACE_NAME)
    print(f"✅ 네임스페이스 생성: {NAMESPACE_NAME}")
else:
    print(f"✅ 네임스페이스 존재: {NAMESPACE_NAME}")

def create_table(table_name: str, schema_fields):
    full_table_name = f"{NAMESPACE_NAME}.{table_name}"
    existing = [".".join(t) for t in catalog.list_tables(NAMESPACE_NAME)]
    if full_table_name in existing:
        print(f"✅ 테이블 이미 존재: {full_table_name}")
    else:
        schema = pa.schema(schema_fields)
        catalog.create_table(full_table_name, schema=schema)
        print(f"✅ 테이블 생성: {full_table_name}")

create_table("click_events", click_arrow_fields())
create_table("keydown_events", keydown_arrow_fields())

print("🎉 모든 테이블 생성 완료!")