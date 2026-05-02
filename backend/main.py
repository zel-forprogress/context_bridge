"""Context Bridge FastAPI 后端入口"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# 将 src/ 和 backend/ 加入 sys.path
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root / "src"))
sys.path.insert(0, str(_root / "backend"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import agents, conversations, monitor, summaries
from context_bridge.watcher_manager import watcher_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

app = FastAPI(title="Context Bridge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(monitor.router, prefix="/api")
app.include_router(summaries.router, prefix="/api")


@app.on_event("startup")
def on_startup():
    watcher_manager.start()


@app.on_event("shutdown")
def on_shutdown():
    watcher_manager.stop()


@app.get("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
