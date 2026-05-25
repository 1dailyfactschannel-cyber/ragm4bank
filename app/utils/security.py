import re
from app.utils.logging import setup_logger

logger = setup_logger()

# Prompt injection keywords/patterns
PROMPT_INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"ignore the (above|context)",
    r"you are now",
    r"system prompt",
    r"new instructions",
    r"disregard",
    r"override",
    r"\/ignore",
    r"<\|im_start\|>",
    r"<\|system\|>",
]


def sanitize_input(text: str, max_length: int = 2000) -> str:
    """
    Санитизация входных данных:
    - Обрезка до max_length
    - Удаление нулевых байтов
    - Нормализация пробелов
    """
    if not text:
        return ""
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def detect_prompt_injection(text: str) -> bool:
    """
    Базовая защита от prompt injection.
    Возвращает True, если обнаружена подозрительная активность.
    """
    if not text:
        return False
    text_lower = text.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            logger.warning(f"Potential prompt injection detected: {pattern}")
            return True
    return False


def mask_pan(text: str) -> str:
    """
    Маскирование номеров карт (PAN) в тексте.
    Заменяет 13-19 последовательных цифр на ****.
    """
    if not text:
        return text
    # Match 13-19 consecutive digits, possibly with spaces/dashes
    return re.sub(r"\b(?:\d[ -]*?){13,19}\b", lambda m: "****" + m.group(0)[-4:] if len(re.sub(r"[^0-9]", "", m.group(0))) >= 13 else m.group(0), text)


def mask_cvv(text: str) -> str:
    """
    Маскирование CVV/CVC кодов.
    """
    if not text:
        return text
    # Match standalone 3-4 digit codes that look like CVV
    return re.sub(r"\b\d{3,4}\b", "***", text)


def sanitize_for_logs(text: str) -> str:
    """
    Санитизация для логов: маскирует PAN и CVV.
    """
    return mask_cvv(mask_pan(text))
