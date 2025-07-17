---

# 🧊 DataLake Prototype

Redis Stream을 메시지 큐로 활용해 유저 이벤트를 수집하고, Apache Iceberg 테이블에 적재하는 프로토타입 애플리케이션입니다.

로컬 환경에서 Redis와 Iceberg 기반 데이터 레이크를 빠르게 테스트하고 탐색할 수 있도록 구성되어 있으며,
프론트엔드, 백엔드, MQ(메시지 큐), 데이터 레이크, 시각화 대시보드로 이루어져 있습니다.

---

## 📦 기술 스택 및 구성 요소

### 💾 Storage

* **MinIO**

  * S3 호환 오브젝트 스토리지
  * Iceberg 데이터 파일 저장소
  * S3 API 및 웹 콘솔 제공

### 🔗 Message Queue

* **Redis Streams**

  * 유저 이벤트 메시지 큐잉
  * Consumer Group으로 병렬 처리 가능

### 🌐 Frontend

* **React + Next.js**

  * 유저 이벤트를 발생시키는 웹 인터페이스

### 📋 Backend

* **FastAPI**

  * 유저 이벤트 수신
  * Redis Stream에 이벤트 적재

### 🛠️ Data Lake

* **Apache Iceberg (pyiceberg)**

  * 이벤트 데이터를 테이블 포맷으로 저장
  * 버저닝 및 데이터 관리 가능

### 👀 Monitoring

* **Streamlit**

  * Iceberg 데이터 및 메타데이터 시각화
  * `data.py` (데이터 대시보드), `meta.py` (메타데이터 탐색)

---

## 🚀 실행 가이드

### 1️⃣ Storage (MinIO) 실행

```bash
docker run -d --name minio \
  -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  -v $(pwd)/data:/data \
  minio/minio server /data --console-address ":9001"
```

* 🔗 웹 콘솔: [http://localhost:9001](http://localhost:9001)
* 🔗 S3 API: [http://localhost:9000](http://localhost:9000)
* 기본 계정:

  * ID: `minioadmin`
  * PW: `minioadmin`

---

### 2️⃣ MQ (Redis) 실행

```bash
docker run -d --name aix_redis \
  --rm \
  -p 6379:6379 \
  -v $(pwd)/data:/data \
  -v $(pwd)/scratch:/scratch \
  redis:7.4.3
```

* Redis CLI 접속:

```bash
docker exec -it aix_redis redis-cli
```

---

### 3️⃣ Frontend (React + Next.js) 실행

```bash
cd frontend
npm install
npm run dev
```

* 🔗 웹 인터페이스: [http://localhost:3000](http://localhost:3000)

---

### 4️⃣ Backend - 이벤트 Producer 실행

```bash
cd backend
uvicorn producer:app --reload --port 8000
```

* 📋 API 엔드포인트: [http://localhost:8000](http://localhost:8000)

---

### 5️⃣ MQ Consumer (Iceberg 적재) 실행

```bash
cd backend/mq_redis
python consumer.py
```

---

### 6️⃣ 대시보드 (Streamlit) 실행

#### 📊 데이터 대시보드

```bash
streamlit run data.py
```

* 🔗 [http://localhost:8501](http://localhost:8501)

#### 🗂️ 메타데이터 탐색기

```bash
streamlit run meta.py
```

* 🔗 [http://localhost:8501](http://localhost:8501)

---

## 📂 폴더 구조

```
.
├── backend/                   # FastAPI 서버
│   ├── producer.py            # 이벤트 수신 API
│   └── mq_redis/
│       └── consumer.py        # Redis → Iceberg 컨슈머
├── frontend/                  # Next.js 프론트엔드
│   └── app/
│       └── page.tsx
├── data.py                    # Streamlit - 데이터 대시보드
├── meta.py                    # Streamlit - 메타데이터 탐색기
├── README.md                  # 문서
├── warehouse/                 # Iceberg 메타데이터 저장소
│   ├── pyiceberg_catalog.db
│   └── mouse_events.db/…
```

---

## 📝 참고 사항

* Iceberg 메타데이터는 **로컬 SQLite**에 저장됩니다.
* 데이터 파일은 \*\*MinIO(S3 호환 오브젝트 스토리지)\*\*에 저장됩니다.
* 유저 이벤트는 **Redis Stream**에 쌓이고, Consumer가 이를 읽어 Iceberg에 적재합니다.
* `data.py`, `meta.py`는 Iceberg 테이블의 **데이터 및 메타데이터 시각화**를 제공합니다.

---

## 🧪 빠른 테스트 및 실험

이 프로젝트는 **이벤트 기반 데이터 레이크 구조**를 빠르게 실험해보고 학습하고자 하는 개발자에게 적합합니다.

* 이벤트 수집부터 분석까지 **로컬 환경**에서 완전한 플로우 테스트 가능
* Redis Stream 기반 MQ → Iceberg 저장까지의 프로세스 구현 예시
* Streamlit 대시보드를 통한 데이터 탐색 및 시각화
