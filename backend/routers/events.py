from fastapi import APIRouter, Request
from services.stream_writer import write_to_stream

router = APIRouter()

@router.post("")
async def receive_event(request: Request):
    data = await request.json()
    print(f"📋 수신된 이벤트: {data}")    
    result = await write_to_stream(data)
    return result