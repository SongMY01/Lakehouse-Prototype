---

# 🧊 Iceberg Prototype

유저 이벤트 데이터를 수집하고, Apache Iceberg 테이블에 적재하는 프로토타입 애플리케이션입니다.
프론트엔드, 백엔드, 데이터 레이크(스토리지) 및 모니터링 대시보드로 구성되어 있으며,
로컬 환경에서 Iceberg 기반 데이터 레이크를 빠르게 테스트하고 탐색할 수 있습니다.

---

## 📦 시스템 구성

| 역할                    | 기술 스택                        |
| --------------------- | ---------------------------- |
| **Frontend**          | React, Next.js               |
| **Backend**           | FastAPI                      |
| **Table Format**      | Apache Iceberg (`pyiceberg`) |
| **Storage**           | MinIO (S3 호환 오브젝트 스토리지)      |
| **Dashboard (데이터)**   | Streamlit (`data.py`)        |
| **Dashboard (메타데이터)** | Streamlit (`meta.py`)        |

---

## 🚀 실행 가이드

### 1️⃣ Storage (MinIO) 실행

MinIO를 로컬에서 Docker로 실행합니다.
데이터 파일은 지정된 디렉토리에 저장되며, S3 API 및 웹 콘솔을 제공합니다.

```bash
docker run -d --name minio \
  -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  -v /Users/minyoung.song/projects/bmp/workspace/my-project/data:/data \
  minio/minio server /data --console-address ":9001"
```

* **콘솔 UI**: [http://localhost:9001](http://localhost:9001)
* **S3 API**: [http://localhost:9000](http://localhost:9000)
* **기본 계정**

  * ID: `minioadmin`
  * PW: `minioadmin`

---

### 2️⃣ Backend (FastAPI) 실행

백엔드 애플리케이션을 `uvicorn`으로 실행합니다.

```bash
cd backend
uvicorn main:app --reload --port 8000
```

* API 엔드포인트: [http://localhost:8000](http://localhost:8000)

---

### 3️⃣ Frontend (React + Next.js) 실행

프론트엔드 애플리케이션을 실행합니다.

```bash
cd frontend
npm install
npm run dev
```

* 웹 인터페이스: [http://localhost:3000](http://localhost:3000)

---

### 4️⃣ Dashboard (Streamlit) 실행

#### 🔷 데이터 대시보드 (`data.py`)

Iceberg 테이블의 **최신 이벤트 데이터**를 확인하고 시계열 분포를 시각화합니다.

```bash
streamlit run data.py
```

* 웹 대시보드: [http://localhost:8501](http://localhost:8501)

---

#### 🔷 메타데이터 탐색기 (`meta.py`)

Iceberg 테이블의 메타데이터 및 파일 상태를 탐색합니다.
metadata.json, manifest list, manifest 파일, parquet 데이터 파일까지 탐색할 수 있습니다.

```bash
streamlit run meta.py
```

* 웹 대시보드: [http://localhost:8501](http://localhost:8501)

---

## 🔗 주요 라이브러리 & 문서

* [FastAPI](https://fastapi.tiangolo.com/) - 백엔드 API 프레임워크
* [pyiceberg](https://py.iceberg.apache.org/) - Python용 Apache Iceberg 클라이언트
* [MinIO](https://min.io/) - 고성능 S3 호환 오브젝트 스토리지
* [React](https://reactjs.org/) - 프론트엔드 UI 라이브러리
* [Next.js](https://nextjs.org/) - React 기반 SSR/SSG 프레임워크
* [Streamlit](https://streamlit.io/) - 빠른 대시보드 빌더

---

## 📂 폴더 구조

```bash
.
├── backend/               # FastAPI 서버
│   └── main.py
├── frontend/              # Next.js 프론트엔드
│   └── app/page.tsx
├── data.py                # Streamlit - 데이터 대시보드
├── meta.py                # Streamlit - 메타데이터 탐색기
├── README.md              # 문서
├── warehouse/             # Iceberg 메타데이터 저장소
│   └── pyiceberg_catalog.db
│   └── mouse_events.db/…
```

---

## 📝 참고 사항

* Iceberg 메타데이터는 로컬의 SQLite에 저장됩니다.
* 데이터 파일은 MinIO(S3 호환 오브젝트 스토리지)에 저장됩니다.
* `data.py`와 `meta.py`는 Iceberg 테이블의 **데이터와 메타데이터 상태를 빠르게 확인**하는 데 유용합니다.

---

## 💡 Notes

* `copy-on-write` 및 `merge-on-read` 전략을 테스트하기 적합합니다.
* 다양한 Iceberg 기능을 학습하고 실습하는 데 도움이 됩니다.
* Kubernetes 및 클라우드 환경으로 확장할 수도 있습니다.
