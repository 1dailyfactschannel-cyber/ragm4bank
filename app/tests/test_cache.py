import pytest
from app.utils.cache import cache, make_key


class TestCache:
    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        await cache.set("test_key", "test_value", ttl=60)
        value = await cache.get("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        await cache.set("del_key", "val", ttl=60)
        await cache.delete("del_key")
        value = await cache.get("del_key")
        assert value is None

    def test_make_key(self):
        key = make_key("prefix", "hello", 123)
        assert key.startswith("prefix:")
        assert len(key) > len("prefix:")
