from database.redis import r

MAX_STREAM_LENGTH = 10000

async def write_to_stream(data: dict):
    # event_type이 없으면 "unknown"으로 처리
    event_type = data.get("event_type", "unknown")

    # Redis가 허용하는 타입으로 변환 (모든 값을 str로)
    data_str = {k: str(v) for k, v in data.items()}

    # Stream 이름 결정
    stream_name = f"{event_type}_events"

    r.xadd(
        stream_name,
        data_str, # type: ignore
        maxlen=MAX_STREAM_LENGTH,
        approximate=True
    )

    return {
        "status": "queued",
        "event_type": event_type,
        "stream": stream_name,
        "received": data
    }