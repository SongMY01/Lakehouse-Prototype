from pydantic import BaseModel
from typing import Optional, List, Tuple
import pyarrow as pa

class KeydownEvent(BaseModel):
    altKey: Optional[bool] = False
    ctrlKey: Optional[bool] = False
    metaKey: Optional[bool] = False
    shiftKey: Optional[bool] = False
    timestamp: int
    type: str

    event_type: str = "keydown"
    key: str
    code: str

def keydown_arrow_fields() -> List[Tuple[str, pa.DataType]]:
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