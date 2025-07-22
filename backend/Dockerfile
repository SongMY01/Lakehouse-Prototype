# backend/Dockerfile

FROM python:3.13-slim
WORKDIR /app

COPY . .

# uv 설치 & pyproject.toml의 의존성 설치
RUN pip install --upgrade pip \
    && pip install uv \
    && uv pip install --system . 

# 로컬과 동일하게 uv로 실행
CMD ["uv", "run", "main.py"]
