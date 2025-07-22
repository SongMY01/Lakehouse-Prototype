FROM python:3.11-slim

WORKDIR /app

COPY backend/ /app

RUN pip install --upgrade pip uv \
    && uv pip install -r requirements.txt

CMD ["uv", "run", "main.py"]