import pytest
from app.utils.retry import async_retry


class TestRetry:
    @pytest.mark.asyncio
    async def test_retry_success(self):
        call_count = 0

        @async_retry(max_retries=3)
        async def success():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await success()
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_eventual_success(self):
        call_count = 0

        @async_retry(max_retries=3, backoff_base=0.01)
        async def eventual():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"

        result = await eventual()
        assert result == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        call_count = 0

        @async_retry(max_retries=2, backoff_base=0.01)
        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("fail")

        with pytest.raises(ValueError):
            await always_fail()
        assert call_count == 2
