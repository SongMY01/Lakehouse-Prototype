# -*- coding: utf-8 -*-
# file: create_iceberg_tables.py
# desc: PyIceberg로 click_events, keydown_events 테이블 생성
# author: 송민영
# created: 2025-07-25

from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema, NestedField
from pyiceberg.types import BooleanType, IntegerType, StringType, TimestampType


def define_click_schema():
    return Schema(
        NestedField(1, "altKey", BooleanType(), required=True),
        NestedField(2, "ctrlKey", BooleanType(), required=True),
        NestedField(3, "metaKey", BooleanType(), required=True),
        NestedField(4, "shiftKey", BooleanType(), required=True),
        NestedField(5, "button", IntegerType(), required=True),
        NestedField(6, "buttons", IntegerType(), required=True),
        NestedField(7, "clientX", IntegerType(), required=True),
        NestedField(8, "clientY", IntegerType(), required=True),
        NestedField(9, "pageX", IntegerType(), required=True),
        NestedField(10, "pageY", IntegerType(), required=True),
        NestedField(11, "screenX", IntegerType(), required=True),
        NestedField(12, "screenY", IntegerType(), required=True),
        NestedField(13, "relatedTarget", StringType(), required=True),
        NestedField(14, "timestamp", TimestampType(), required=True),
        NestedField(15, "type", StringType(), required=True),
    )


def define_keyboard_schema():
    return Schema(
        NestedField(1, "altKey", BooleanType(), required=True),
        NestedField(2, "ctrlKey", BooleanType(), required=True),
        NestedField(3, "metaKey", BooleanType(), required=True),
        NestedField(4, "shiftKey", BooleanType(), required=True),
        NestedField(5, "key", StringType(), required=True),
        NestedField(6, "code", StringType(), required=True),
        NestedField(7, "timestamp", TimestampType(), required=True),
        NestedField(8, "type", StringType(), required=True),
    )


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

    catalog = load_catalog("default")  

    create_table(catalog, "user_events.click_events", define_click_schema())
    create_table(catalog, "user_events.keydown_events", define_keyboard_schema())

    print("✅ Iceberg 테이블 생성 완료!")


if __name__ == "__main__":
    main()