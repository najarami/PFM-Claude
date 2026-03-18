from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import *  # noqa: F401, F403 - register all models


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Finanzas Personales API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import accounts, budget, comparison, fx, summary, transactions, upload  # noqa: E402

app.include_router(accounts.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(summary.router, prefix="/api")
app.include_router(comparison.router, prefix="/api")
app.include_router(budget.router, prefix="/api")
app.include_router(fx.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
