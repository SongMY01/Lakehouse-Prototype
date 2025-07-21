import redis
import logging
logger = logging.getLogger(__name__)
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    logger.info("✅ Redis 연결 성공")
except Exception as e:
    logger.error(f"🚨 Redis 연결 실패: {e}")
