from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.models import DocumentChunk, Document
from app.config import settings
from app.utils.logging import setup_logger
from typing import List, Tuple
logger = setup_logger()


class Retriever:
    def __init__(self):
        self.top_k = settings.TOP_K
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD

    async def search_similar_chunks(
        self,
        db: AsyncSession,
        query_embedding: List[float],
        top_k: int = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Ищет наиболее похожие чанки используя pgvector cosine similarity.
        cosine_distance = 1 - cosine_similarity, поэтому similarity = 1 - distance.
        """
        k = top_k or self.top_k

        # Используем pgvector cosine_distance в ORDER BY и вычисляем similarity = 1 - distance
        distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding)
        query = (
            select(DocumentChunk, distance_expr.label("distance"))
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.is_active == True)
            .order_by(distance_expr)
            .limit(k * 2)
        )

        result = await db.execute(query)

        results_with_scores = []
        for chunk, distance in result.all():
            similarity = 1.0 - float(distance)
            if similarity >= self.similarity_threshold:
                results_with_scores.append((chunk, similarity))

        # Сортируем по similarity и возвращаем top_k
        results_with_scores.sort(key=lambda x: x[1], reverse=True)
        return results_with_scores[:k]
    
    async def get_context_from_chunks(
        self, 
        chunks_with_scores: List[Tuple[DocumentChunk, float]]
    ) -> str:
        """
        Формирует контекст для LLM из найденных чанков
        """
        context_parts = []
        
        for chunk, score in chunks_with_scores:
            context_parts.append(
                f"[Source: {chunk.document.title}, Score: {score:.2f}]\n{chunk.chunk_text}"
            )
        
        return "\n\n".join(context_parts)
