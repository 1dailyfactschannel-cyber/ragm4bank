import httpx
from app.config import settings
from app.utils.logging import setup_logger

logger = setup_logger()

ALERT_STATES = {
    "ollama_downtime": False,
    "db_downtime": False,
    "low_similarity": False,
    "high_fallback_queue": False,
}


async def send_telegram_alert(message: str):
    """
    Отправляет alert в Telegram админам (через BOT API).
    Для production настройте ADMIN_CHAT_IDS в .env.
    """
    admin_chat_ids = getattr(settings, 'ADMIN_CHAT_IDS', '')
    if not admin_chat_ids or not settings.BOT_TOKEN:
        logger.warning(f"ALERT (not sent, no config): {message}")
        return

    chat_ids = [c.strip() for c in admin_chat_ids.split(",")]
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"

    for chat_id in chat_ids:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(url, json={"chat_id": chat_id, "text": f"🚨 RAG Alert:\n{message}"})
        except Exception as e:
            logger.error(f"Failed to send alert to {chat_id}: {e}")


async def check_alerts(db_status: str, ollama_status: str, avg_similarity: float, queue_size: int):
    """
    Проверяет условия для алертов:
    - DB downtime > 1 min (упрощенно: статус unhealthy)
    - Ollama downtime > 2 min (упрощенно: статус unhealthy)
    - Median similarity < 0.6
    - Fallback queue size > 20
    """
    if db_status == "unhealthy" and not ALERT_STATES["db_downtime"]:
        ALERT_STATES["db_downtime"] = True
        await send_telegram_alert("Database is DOWN!")
    elif db_status == "ok":
        ALERT_STATES["db_downtime"] = False

    if ollama_status == "unhealthy" and not ALERT_STATES["ollama_downtime"]:
        ALERT_STATES["ollama_downtime"] = True
        await send_telegram_alert("Ollama is DOWN!")
    elif ollama_status == "ok":
        ALERT_STATES["ollama_downtime"] = False

    if avg_similarity < 0.6 and not ALERT_STATES["low_similarity"]:
        ALERT_STATES["low_similarity"] = True
        await send_telegram_alert(f"Median similarity is LOW: {avg_similarity:.3f}")
    elif avg_similarity >= 0.6:
        ALERT_STATES["low_similarity"] = False

    if queue_size > 20 and not ALERT_STATES["high_fallback_queue"]:
        ALERT_STATES["high_fallback_queue"] = True
        await send_telegram_alert(f"Fallback queue is HIGH: {queue_size} items")
    elif queue_size <= 20:
        ALERT_STATES["high_fallback_queue"] = False
