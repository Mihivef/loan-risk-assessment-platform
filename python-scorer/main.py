

from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers.score_router import router as score_router
from db.database import migrate, close_pool


@asynccontextmanager
async def lifespan(app: FastAPI):

    print(" Python scorer starting...")
    try:
        await migrate()
    except Exception as e:
        print(f" DB migration skipped (running without DB?): {e}")
    yield
    print(" Shutting down...")
    await close_pool()


app = FastAPI(
    title="Loan Risk ML Scorer",
    description="ML credit risk scoring and fraud detection for IDFC loan platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(score_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "python-scorer",
        "port": 8000,
        "endpoints": [
            "POST /score/credit-risk",
            "POST /score/fraud-check",
            "GET  /score/factors/{app_id}",
        ],
    }
