"""
Model de Tarefa - IdeiaTech
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.models.user import Base


class TaskStatus(str, enum.Enum):
    """Status da tarefa"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskPriority(str, enum.Enum):
    """Prioridade da tarefa"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base):
    """Model de Tarefa"""
    __tablename__ = "tasks"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status e prioridade
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    
    # Atribuição
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Tempo estimado e real
    estimated_hours = Column(Float, nullable=True)  # Tempo estimado em horas
    actual_hours = Column(Float, default=0.0, nullable=False)  # Tempo real gasto
    
    # Skills necessárias (JSON string)
    required_skills = Column(Text, nullable=True)  # Lista de skills em JSON
    
    # Datas
    due_date = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # IA Recommendation Score
    ai_match_score = Column(Float, nullable=True)  # Score de match da IA (0-100)
    ai_recommendation_reason = Column(Text, nullable=True)  # Justificativa da IA
    
    # Relacionamentos
    assigned_user = relationship("User", back_populates="tasks_assigned", foreign_keys=[assigned_to])
    creator = relationship("User", back_populates="tasks_created", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    @property
    def is_overdue(self) -> bool:
        """Verifica se a tarefa está atrasada"""
        if not self.due_date:
            return False
        return datetime.now() > self.due_date and self.status != TaskStatus.COMPLETED
    
    @property
    def progress_percentage(self) -> float:
        """Calcula progresso baseado em horas"""
        if not self.estimated_hours or self.estimated_hours == 0:
            return 0.0
        return min(100.0, (self.actual_hours / self.estimated_hours) * 100)
