from pydantic import BaseModel
from typing import Optional, List, Tuple
import pyarrow as pa

class ClickEvent(BaseModel):
    altKey: Optional[bool] = False
    ctrlKey: Optional[bool] = False
    metaKey: Optional[bool] = False
    shiftKey: Optional[bool] = False
    timestamp: int
    type: str

    event_type: str = "click"
    button: Optional[int]
    buttons: Optional[int]
    clientX: Optional[int]
    clientY: Optional[int]
    pageX: Optional[int]
    pageY: Optional[int]
    screenX: Optional[int]
    screenY: Optional[int]
    relatedTarget: Optional[str]

def click_arrow_fields() -> List[Tuple[str, pa.DataType]]:
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
        ("relatedTarget", pa.string()),
        ("timestamp", pa.timestamp("ms")),
        ("type", pa.string()),
    ]