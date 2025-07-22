FROM python:3.11-slim

WORKDIR /app

COPY streamlit/ /app

RUN pip install --upgrade pip uv \
    && uv pip install streamlit

CMD ["uv", "streamlit", "run", "data.py", "--server.port=8501", "--server.address=0.0.0.0"]