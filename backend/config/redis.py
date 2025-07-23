# -*- coding: utf-8 -*-
# file: config/redis.py
# desc: Redis 연결 설정 및 헬스 체크
# author: minyoung.song
# created: 2025-07-23

import redis
import logging

logger = logging.getLogger(__name__)

try:
    # Redis 클라이언트 초기화 (sv_redis:6379에 연결, 응답은 문자열로 디코딩)
    r = redis.Redis(host='sv_redis', port=6379, decode_responses=True)
    
    # Redis에 ping을 보내 연결 상태 확인
    r.ping()
    logger.info("✅ Redis 연결 성공")
except Exception as e:
    logger.error(f"🚨 Redis 연결 실패: {e}")