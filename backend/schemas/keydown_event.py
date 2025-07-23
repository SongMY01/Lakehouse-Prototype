# -*- coding: utf-8 -*-
# file: schemas/keydown_event.py
# desc: 키다운 이벤트 스키마 정의 및 PyArrow 필드 매핑 함수
# author: minyoung.song
# created: 2025-07-23

from pydantic import BaseModel
from typing import Optional, List, Tuple
import pyarrow as pa

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