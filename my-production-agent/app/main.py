import time
import signal
import logging
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from app.config import settings
from app.auth import verify_api_key
from app.rate_limiter import check_rate_limit
from app.cost_guard import check_budget, record_usage

logging.basicConfig(
    level=settings.log_level,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
is_ready = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global is_ready
    logger.info(json.dumps({"event": "startup", "app": settings.app_name}))
    is_ready = True
    yield
    is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str
    user_id: str = "default"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def ready():
    if not is_ready:
        raise HTTPException(503, "Not ready")
    return {"ready": True}


@app.post("/ask")
def ask(
    body: AskRequest,
    user_id: str = Depends(verify_api_key),
):
    check_rate_limit(user_id)
    check_budget(user_id)

    # Mock LLM response
    answer = f"[Mock] Answer to: {body.question}"

    record_usage(user_id, input_tokens=len(body.question.split()) * 2, output_tokens=20)

    logger.info(json.dumps({"event": "ask", "user_id": user_id, "q_len": len(body.question)}))

    return {
        "question": body.question,
        "answer": answer,
        "user_id": user_id,
    }


def handle_sigterm(*args):
    logger.info("Received SIGTERM — shutting down gracefully")


signal.signal(signal.SIGTERM, handle_sigterm)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
    )
