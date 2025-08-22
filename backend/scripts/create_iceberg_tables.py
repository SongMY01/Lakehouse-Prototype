# -*- coding: utf-8 -*-
# file: create_iceberg_tables.py
# desc: PyIceberg로 click_events, keydown_events 테이블 생성
# author: 송민영
# created: 2025-07-25

from pyiceberg.schema import Schema
from config.iceberg import catalog
from schemas.mouse_event import define_mouse_schema
from schemas.keydown_event import define_keyboard_schema

# Map event types to their schema functions
EVENT_SCHEMAS = [
    # ("mouse", define_mouse_schema),
    # ("keydown", define_keyboard_schema),
    ("events_bronze", define_keyboard_schema),
]


def create_table(catalog, table_name: str, schema: Schema):
    try:
        print(f"📦 Dropping existing table: {table_name}")
        catalog.drop_table(table_name)
    except Exception:
        print(f"ℹ️  Table {table_name} does not exist or could not be dropped.")

    print(f"✅ Creating table: {table_name}")
    catalog.create_table(table_name, schema=schema)


def main():
    print("📚 Loading Iceberg catalog...")

    for event, schema_fn in EVENT_SCHEMAS:
        table_name = f"user_events.{event}"
        create_table(catalog, table_name, schema_fn())

    print("✅ Iceberg 테이블 생성 완료!")


if __name__ == "__main__":
    main()
