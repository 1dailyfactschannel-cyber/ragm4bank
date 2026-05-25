import pytest
from app.utils.metrics import rag_requests_total, rag_fallback_total, rag_response_time_seconds, rag_similarity_score


class TestMetrics:
    def test_counter_inc(self):
        before = rag_requests_total.labels(status="answered")._value.get()
        rag_requests_total.labels(status="answered").inc()
        after = rag_requests_total.labels(status="answered")._value.get()
        assert after > before

    def test_fallback_counter(self):
        before = rag_fallback_total._value.get()
        rag_fallback_total.inc()
        after = rag_fallback_total._value.get()
        assert after > before

    def test_histogram_observe(self):
        rag_response_time_seconds.observe(1.5)
        rag_similarity_score.observe(0.75)
        # Basic smoke test that no exception is raised
        assert True
