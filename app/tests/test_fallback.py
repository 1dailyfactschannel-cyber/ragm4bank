import pytest
from app.api.routes.fallback import router


class TestFallback:
    def test_router_exists(self):
        assert router is not None
        assert len(router.routes) > 0
