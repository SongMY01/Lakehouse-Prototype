# -*- coding: utf-8 -*-
# file: create_iceberg_tables.py
# desc: PyIceberg로 click_events, keydown_events 테이블 생성
# author: 송민영
# created: 2025-07-25

from pyiceberg.schema import Schema
from config.iceberg import catalog
from schemas.click_event import define_click_schema
from schemas.keydown_event import define_keyboard_schema


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

    create_table(catalog, "user_events.click_events", define_click_schema())
    create_table(catalog, "user_events.keydown_events", define_keyboard_schema())

    print("✅ Iceberg 테이블 생성 완료!")


if __name__ == "__main__":
    main()
