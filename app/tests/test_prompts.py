import pytest
from app.prompts.system_prompt import SYSTEM_PROMPT


class TestSystemPrompt:
    def test_prompt_not_empty(self):
        assert len(SYSTEM_PROMPT) > 0
    
    def test_prompt_contains_rules(self):
        assert "ОТВЕТ ТОЛЬКО НА ОСНОВЕ КОНТЕКСТА" in SYSTEM_PROMPT
        assert "ПРАВИЛО ОТКАЗА" in SYSTEM_PROMPT
        assert "ЗАПРЕЩЕННЫЕ ТЕМЫ" in SYSTEM_PROMPT
        assert "БЕЗОПАСНОСТЬ" in SYSTEM_PROMPT
        assert "ТОЧНОСТЬ ЦИФР" in SYSTEM_PROMPT
    
    def test_prompt_contains_fallback_template(self):
        assert "[ПЕРЕДАТЬ_ОПЕРАТОРУ]" in SYSTEM_PROMPT
    
    def test_prompt_contains_style_guidelines(self):
        assert "Тон:" in SYSTEM_PROMPT
        assert "Структура:" in SYSTEM_PROMPT
        assert "Пошаговость:" in SYSTEM_PROMPT
