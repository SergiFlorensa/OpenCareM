"""
Modelos de base de datos para guardar corridas de agentes y trazas por paso.
"""
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class AgentRun(Base):
    """Representa una ejecucion completa de un workflow de agente."""

    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_name = Column(String(100), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    run_input = Column(JSON, nullable=False)
    run_output = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    total_cost_usd = Column(Float, nullable=False, default=0.0, server_default="0")
    total_latency_ms = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self):
        return (
            f"AgentRun(id={self.id}, workflow_name='{self.workflow_name}', "
            f"status='{self.status}', total_latency_ms={self.total_latency_ms})"
        )


class AgentStep(Base):
    """Guarda un paso trazable dentro de una ejecucion de agente."""

    __tablename__ = "agent_steps"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(
        Integer,
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_order = Column(Integer, nullable=False)
    step_name = Column(String(100), nullable=False)
    status = Column(String(32), nullable=False, index=True)
    step_input = Column(JSON, nullable=False)
    step_output = Column(JSON, nullable=True)
    decision = Column(Text, nullable=True)
    fallback_used = Column(Boolean, nullable=False, default=False, server_default="0")
    error_message = Column(Text, nullable=True)
    step_cost_usd = Column(Float, nullable=False, default=0.0, server_default="0")
    step_latency_ms = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self):
        return (
            f"AgentStep(id={self.id}, run_id={self.run_id}, step_order={self.step_order}, "
            f"status='{self.status}', fallback_used={self.fallback_used})"
        )
