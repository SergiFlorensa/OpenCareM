"""
Modelo para auditoria de consultas RAG.
"""
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class RAGQueryAudit(Base):
    """Audita cada consulta RAG realizada en el sistema."""

    __tablename__ = "rag_queries_audit"

    id = Column(Integer, primary_key=True, index=True)
    care_task_id = Column(
        Integer,
        ForeignKey("care_tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    query = Column(Text, nullable=False)
    search_method = Column(String(32), nullable=False)
    chunks_retrieved = Column(Integer, nullable=False, default=0)
    vector_search_latency_ms = Column(Float, nullable=True)
    keyword_search_latency_ms = Column(Float, nullable=True)
    total_latency_ms = Column(Float, nullable=True)
    model_used = Column(String(64), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"RAGQueryAudit(id={self.id}, task_id={self.care_task_id}, "
            f"method='{self.search_method}', chunks={self.chunks_retrieved})"
        )
