import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import events

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="My Project API",
    description="FastAPI application entry point",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(events.router, prefix="/api/events", tags=["Events"])


@app.get("/")
async def root():
    logger.info("루트 엔드포인트 호출됨")
    return {"message": "Hello from FastAPI!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)