# backend/Dockerfile

FROM python:3.13-slim
WORKDIR /app

# (선택) 빌드 시 필요한 시스템 패키지가 없으면 주석 해제
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     ca-certificates curl && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --upgrade pip \
    && pip install uv \
    && uv pip install --system . \
    && uv pip install --system \
         "gunicorn>=21.2" \
         "uvicorn[standard]>=0.30" \
         "orjson>=3.10"

# ✅ Gunicorn로 애플리케이션 실행
CMD ["gunicorn", "main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "8", \
     "--keep-alive", "30", \
     "--timeout", "0", \
     "--graceful-timeout", "30", \
     "--log-level", "warning", \
     "--access-logfile", "/dev/null", \
     "--error-logfile", "-"]
