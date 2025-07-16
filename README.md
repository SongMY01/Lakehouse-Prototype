---

# 🧊 Iceberg Prototype

유저 이벤트를 수집하여 Apache Iceberg 테이블에 적재하는 프로토타입입니다.
프론트엔드, 백엔드, 스토리지가 구성되어 있습니다.

---

## 📦 구성

| 역할           | 기술 스택          |
| ------------ | -------------- |
| **Frontend** | React, Next.js |
| **Backend**  | FastAPI        |
| **Iceberg**  | pyiceberg      |
| **Storage**  | MinIO          |

---

## 🚀 실행 방법

### 1️⃣ Storage (MinIO) 실행

로컬에서 MinIO를 Docker로 실행합니다.
데이터는 지정된 디렉토리에 저장됩니다.

```bash
docker run -d --name minio \
  -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  -v /Users/minyoung.song/projects/bmp/workspace/my-project/data:/data \
  minio/minio server /data --console-address ":9001"
```

* 콘솔: [http://localhost:9001](http://localhost:9001)
* API 엔드포인트: [http://localhost:9000](http://localhost:9000)
* 기본 계정:

  * ID: `minioadmin`
  * PW: `minioadmin`

---

### 2️⃣ Backend (FastAPI) 실행

`uvicorn`으로 서버를 실행합니다.

```bash
uvicorn main:app --reload --port 8000
```

* API 엔드포인트: [http://localhost:8000](http://localhost:8000)

---

### 3️⃣ Frontend (React + Next.js)

프로젝트 디렉토리에서 실행합니다.

```bash
npm install
npm run dev
```

* 프론트엔드: [http://localhost:3000](http://localhost:3000)

---

## 🔗 주요 라이브러리

* [FastAPI](https://fastapi.tiangolo.com/)
* [pyiceberg](https://py.iceberg.apache.org/)
* [MinIO](https://min.io/)
* [React](https://reactjs.org/)
* [Next.js](https://nextjs.org/)

---

## 📄 폴더 구조 예시

```
.
├── backend/
│   └── main.py
├── frontend/
│   └── (Next.js 프로젝트)
├── README.md
```

---

### ✨ 참고

* Iceberg 메타데이터는 로컬의 SQLite에 저장됩니다.
* 데이터 파일은 MinIO(S3 호환)에 저장됩니다.

---
