# -*- coding: utf-8 -*-
# file: schemas/keydown_event.py
# desc: 키다운 이벤트 스키마 정의 및 Iceberg 필드 매핑 함수
# author: minyoung.song
# created: 2025-07-23

from pydantic import BaseModel
from typing import Optional, List, Tuple
import pyarrow as pa
from pyiceberg.schema import Schema, NestedField
from pyiceberg.types import BooleanType, StringType, TimestampType

class KeydownEvent(BaseModel):
    """
    클라이언트로부터 수신한 키다운 이벤트 데이터를 표현하는 Pydantic 모델
    """
    # Modifier Keys
    altKey: Optional[bool] = False
    ctrlKey: Optional[bool] = False
    metaKey: Optional[bool] = False
    shiftKey: Optional[bool] = False

    # 이벤트 발생 시각 및 타입
    timestamp: int
    type: str

    # 고정 이벤트 타입 및 키 정보
    event_type: str = "keydown"
    key: str
    code: str



def define_keyboard_schema() -> Schema:
    """
    KeydownEvent 스키마를 Iceberg의 Schema 객체로 반환

    Returns:
        Schema: Iceberg 테이블 생성을 위한 스키마 객체
    """
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

def keydown_arrow_fields() -> List[Tuple[str, pa.DataType]]:
    """
    KeydownEvent 스키마를 PyArrow 필드 정의 리스트로 반환

    Returns:
        List[Tuple[str, pa.DataType]]: (필드명, 데이터 타입) 튜플의 리스트
    """
    return [
        ("altKey", pa.bool_()),
        ("ctrlKey", pa.bool_()),
        ("metaKey", pa.bool_()),
        ("shiftKey", pa.bool_()),
        ("key", pa.string()),
        ("code", pa.string()),
        ("timestamp", pa.timestamp("ms")),
        ("type", pa.string()),
    ]