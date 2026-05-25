from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from app.utils.logging import setup_logger

logger = setup_logger()

# Counters
rag_requests_total = Counter(
    'rag_requests_total',
    'Total RAG requests',
    ['status']
)

rag_fallback_total = Counter(
    'rag_fallback_total',
    'Total fallback requests'
)

# Histograms
rag_response_time_seconds = Histogram(
    'rag_response_time_seconds',
    'Response time in seconds',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

rag_similarity_score = Histogram(
    'rag_similarity_score',
    'Similarity score distribution',
    buckets=[0.0, 0.3, 0.5, 0.6, 0.65, 0.7, 0.8, 0.9, 1.0]
)

ollama_request_duration_seconds = Histogram(
    'ollama_request_duration_seconds',
    'Ollama request duration',
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Gauges
db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Current DB connection pool size'
)

fallback_queue_size = Gauge(
    'fallback_queue_size',
    'Current fallback queue size'
)


def metrics_response():
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
