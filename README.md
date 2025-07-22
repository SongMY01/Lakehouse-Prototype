# 🪄 Lakehouse Prototype

Modern, event-driven Lakehouse stack.  
FastAPI + Redis + Iceberg + Streamlit + Next.js — all orchestrated with Docker.

---

## 📁 Project Structure

```
my-project/
├── backend/              # FastAPI + Event Loader + Streamlit
│   ├── main.py
│   ├── Dockerfile
│   ├── Dockerfile.event_loader
│   ├── Dockerfile.streamlit
│   ├── pyproject.toml
│   ├── scripts/
│   │   └── create_table.py
│   ├── config/
│   │   ├── iceberg.py
│   │   └── redis.py
│   ├── routers/
│   │   └── events.py
│   ├── schemas/
│   │   ├── click_event.py
│   │   └── keydown_event.py
│   ├── services/
│   │   ├── event_loader.py
│   │   └── stream_writer.py
│   ├── streamlit/
│   │   └── main.py
│   └── db/
│       ├── warehouse/        # Iceberg metadata
│       ├── minIO/data/
│       └── redis/data/
├── frontend/             # Next.js
│   ├── app/page.tsx
│   ├── Dockerfile
│   ├── next.config.ts
│   ├── public/
│   └── tsconfig.json
├── docker-compose.yml
└── README.md
```

---

## 🚀 Tech Stack

✅ API: FastAPI  
✅ Events: Redis Streams  
✅ Lakehouse: Iceberg + PyArrow + MinIO (S3-compatible)  
✅ Dashboard: Streamlit  
✅ Frontend: Next.js  
✅ Orchestration: Docker Compose  
✅ Package Management: uv  

---

## 🧰 How to Run

### 1️⃣ Bootstrap

- Create Docker network:
  ```bash
  docker network create my-network
  ```

- Prepare `.env` in `backend/` with your configs.

---

### 2️⃣ Create MinIO Bucket & Iceberg Tables

- Spin up MinIO & Redis:
  ```bash
  docker compose up -d minio redis
  ```

- Go to [http://localhost:9001](http://localhost:9001) → login (`minioadmin/minioadmin`) → create a bucket named:
  ```
  user-events
  ```

- Initialize Iceberg tables:
  ```bash
  cd backend
  uv run python -m scripts.create_table
  ```

---

### 3️⃣ Run the full stack

```bash
docker compose up -d --build
```

---

### 4️⃣ Access the stack

| Service            | URL                              |
|--------------------|----------------------------------|
| ⚡️ Backend (API)    | [http://localhost:8000](http://localhost:8000) |
| 📊 Streamlit        | [http://localhost:8501](http://localhost:8501) |
| 🌐 Frontend         | [http://localhost:3000](http://localhost:3000) |
| 🗄️ MinIO Console     | [http://localhost:9001](http://localhost:9001) |
| 🪄 Redis CLI         | `redis-cli -h localhost`        |

---

## 💡 Notes

- MinIO bucket must exist before loading data.
- Iceberg metadata lives in `backend/db/warehouse/pyiceberg_catalog.db`.
- Run `create_table.py` after MinIO bucket is ready.
- `.env` is not committed — bring your own.

---
