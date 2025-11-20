"""
Model de Usuário - IdeiaTech
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum


class UserRole(str, enum.Enum):
    """Tipos de usuário no sistema"""
    COLABORADOR = "colaborador"
    GESTOR = "gestor"
    ADMIN = "admin"


class User(Base):
    """Model de Usuário"""
    __tablename__ = "users"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Role e status
    role = Column(SQLEnum(UserRole), default=UserRole.COLABORADOR, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Informações profissionais
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Métricas de trabalho
    workload_capacity = Column(Integer, default=40, nullable=False)  # Horas por semana
    current_workload = Column(Integer, default=0, nullable=False)  # Horas atualmente alocadas
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relacionamentos
    manager = relationship("User", remote_side=[id], backref="subordinates")
    tasks_assigned = relationship("Task", back_populates="assigned_user", foreign_keys="Task.assigned_to")
    tasks_created = relationship("Task", back_populates="creator", foreign_keys="Task.created_by")
    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    wellbeing_checks = relationship("WellbeingCheck", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    @property
    def workload_percentage(self) -> float:
        """Retorna a porcentagem de carga de trabalho"""
        if self.workload_capacity == 0:
            return 0.0
        return (self.current_workload / self.workload_capacity) * 100
    
    @property
    def is_overloaded(self) -> bool:
        """Verifica se o usuário está sobrecarregado"""
        return self.workload_percentage > 90
    
    @property
    def available_hours(self) -> int:
        """Retorna horas disponíveis"""
        return max(0, self.workload_capacity - self.current_workload)


# Base para SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey

Base = declarative_base()
