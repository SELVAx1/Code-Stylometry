from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import auth, groups, submissions, analysis
from app.routers.monitor import router as monitor_router
from app.services.monitor import monitor


@asynccontextmanager
async def lifespan(app):
    await init_db()
    monitor.start()
    yield
    monitor.stop()


app = FastAPI(
    title="Code Stylometry",
    description="Authorship verification and anomaly detection for competitive programming submissions",
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

app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(submissions.router)
app.include_router(analysis.router)
app.include_router(monitor_router)


@app.get("/")
async def root():
    return {
        "name": "Code Stylometry API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
