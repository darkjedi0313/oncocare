from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

load_dotenv()
from api.routers.query import router as query_router
from api.routers.generation import router as generation_router
from api.routers.chat import router as chat_router
from api.routers.auth import router as auth_router

app = FastAPI(
    title="OncoCare API",
    description="공공데이터 결합 기반 국가암검진 예산 배분 진단 및 효과 검증 서비스 API",
    version="0.1.0"
)

# CORS 설정
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(query_router)
app.include_router(generation_router)
app.include_router(chat_router)
app.include_router(auth_router)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "OncoCare API Server is running"}

# 프론트엔드 정적 파일 마운트 (루트 경로)
app.mount("/", StaticFiles(directory="web", html=True), name="web")

