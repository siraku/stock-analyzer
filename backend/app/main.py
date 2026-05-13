from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models import analysis, price_cache, watchlist  # noqa: F401 — register models
from app.routers import analysis as analysis_router
from app.routers import settings, stocks, watchlist as watchlist_router

# Create all DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Stock Reversal Analyzer",
    description="Analyzes equities for trend reversal signals using technical indicators and AI.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(watchlist_router.router)
app.include_router(analysis_router.router)
app.include_router(stocks.router)
app.include_router(settings.router)


@app.get("/")
def root():
    return {"message": "Stock Reversal Analyzer API", "docs": "/docs"}
