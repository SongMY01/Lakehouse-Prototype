import logging
from fastapi import APIRouter, Request
from services.stream_writer import write_to_stream

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("")
async def receive_event(request: Request):
    data = await request.json()
    logger.info(f"/api/events: {data}")
    result = await write_to_stream(data)
    return result