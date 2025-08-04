from pydantic import BaseModel
from pyiceberg.schema import Schema, NestedField
from pyiceberg.types import BooleanType, IntegerType, StringType, TimestampType, DoubleType
from typing import Optional, List, Tuple
import pyarrow as pa


class ClickEvent(BaseModel):
    """
    클라이언트로부터 수신한 클릭 이벤트 데이터를 표현하는 Pydantic 모델
    """
    # modifier keys
    altKey: Optional[bool] = False
    ctrlKey: Optional[bool] = False
    metaKey: Optional[bool] = False
    shiftKey: Optional[bool] = False

    # 이벤트 발생 시각 (ms)
    timestamp: int

    # DOM 이벤트 타입 (예: "click", "mousedown" 등)
    type: str

    # 마우스 관련 좌표 및 버튼 상태
    button: Optional[int]
    buttons: Optional[int]
    clientX: Optional[int]
    clientY: Optional[int]
    pageX: Optional[int]
    pageY: Optional[int]
    screenX: Optional[int]
    screenY: Optional[int]

    # 추가 필드
    canvasId: Optional[str]
    canvasX: Optional[float]
    canvasY: Optional[float]
    movementX: Optional[float]
    movementY: Optional[float]
    isTrusted: Optional[bool]
    shape: Optional[str]


def define_mouse_schema() -> Schema:
    """
    ClickEvent 스키마를 Iceberg의 Schema 객체로 반환

    Returns:
        Schema: Iceberg 테이블 생성을 위한 스키마 객체
    """
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
        NestedField(13, "timestamp", TimestampType(), required=True),
        NestedField(14, "event_type", StringType(), required=True),
        NestedField(15, "canvasId", StringType(), required=False),
        NestedField(16, "canvasX", DoubleType(), required=False),
        NestedField(17, "canvasY", DoubleType(), required=False),
        NestedField(18, "movementX", DoubleType(), required=False),
        NestedField(19, "movementY", DoubleType(), required=False),
        NestedField(20, "isTrusted", BooleanType(), required=False),
        NestedField(21, "shape", StringType(), required=False),
    )

def mouse_arrow_fields() -> List[Tuple[str, pa.DataType]]:
    """
    ClickEvent 스키마를 PyArrow 필드 정의 리스트로 반환

    Returns:
        List[Tuple[str, pa.DataType]]: (필드명, 데이터 타입) 튜플의 리스트
    """
    return [
        ("altKey", pa.bool_()),
        ("ctrlKey", pa.bool_()),
        ("metaKey", pa.bool_()),
        ("shiftKey", pa.bool_()),
        ("button", pa.int32()),
        ("buttons", pa.int32()),
        ("clientX", pa.int32()),
        ("clientY", pa.int32()),
        ("pageX", pa.int32()),
        ("pageY", pa.int32()),
        ("screenX", pa.int32()),
        ("screenY", pa.int32()),
        ("timestamp", pa.timestamp("ms")),
        ("event_type", pa.string()),
        ("canvasId", pa.string()),
        ("canvasX", pa.float64()),
        ("canvasY", pa.float64()),
        ("movementX", pa.float64()),
        ("movementY", pa.float64()),
        ("isTrusted", pa.bool_()),
        ("shape", pa.string()),
    ]