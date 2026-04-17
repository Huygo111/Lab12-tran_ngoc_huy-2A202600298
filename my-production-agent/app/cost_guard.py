import time
from fastapi import HTTPException
from app.config import settings

_usage: dict[str, dict] = {}
PRICE_PER_1K_INPUT = 0.00015
PRICE_PER_1K_OUTPUT = 0.0006


def _get_user(user_id: str) -> dict:
    today = time.strftime("%Y-%m-%d")
    if user_id not in _usage or _usage[user_id]["day"] != today:
        _usage[user_id] = {"day": today, "cost": 0.0}
    return _usage[user_id]


def check_budget(user_id: str) -> None:
    record = _get_user(user_id)
    if record["cost"] >= settings.daily_budget_usd:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Daily budget exceeded",
                "used_usd": record["cost"],
                "budget_usd": settings.daily_budget_usd,
            },
        )


def record_usage(user_id: str, input_tokens: int, output_tokens: int) -> None:
    record = _get_user(user_id)
    cost = (input_tokens / 1000 * PRICE_PER_1K_INPUT +
            output_tokens / 1000 * PRICE_PER_1K_OUTPUT)
    record["cost"] += cost
