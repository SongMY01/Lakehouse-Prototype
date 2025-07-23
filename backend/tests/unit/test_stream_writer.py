
import pytest  # pytest를 import하여 테스트 프레임워크 사용
from unittest.mock import patch, MagicMock  # patch와 MagicMock을 이용해 의존성(Mock) 처리

from services.stream_writer import write_to_stream  # 테스트 대상 함수 import

# anyio를 이용해 비동기 함수 테스트를 가능하게 함
@pytest.mark.anyio
async def test_write_to_stream():
    # 테스트용 데이터 정의
    data = {
        "event_type": "click",
        "altKey": True,
        "clientX": 123
    }

    # Redis 클라이언트를 mock 처리
    with patch("services.stream_writer.r") as mock_r:
        mock_r.xadd = MagicMock()

        # 테스트 대상 함수 호출
        result = await write_to_stream(data)

        # 기대되는 Stream 이름과 데이터 포맷
        stream_name = "click_events"
        data_str = {k: str(v) for k, v in data.items()}
        
        # Redis의 xadd가 정확히 한번 호출되었는지 검증
        mock_r.xadd.assert_called_once_with(
            stream_name,
            data_str,
            maxlen=10000,
            approximate=True
        )

        # 함수의 반환값 검증
        assert result == {
            "status": "queued",
            "event_type": "click",
            "stream": stream_name,
            "received": data
        }