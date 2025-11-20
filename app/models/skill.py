"""
Model de Habilidades - IdeiaTech
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.user import Base


class SkillLevel(str, enum.Enum):
    """Nível de proficiência em uma skill"""
    BEGINNER = "beginner"      # 0-25%
    INTERMEDIATE = "intermediate"  # 26-50%
    ADVANCED = "advanced"      # 51-75%
    EXPERT = "expert"          # 76-100%


class Skill(Base):
    """Model de Habilidade (Skill)"""
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=True)  
    description = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relacionamentos
    user_skills = relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}')>"


class UserSkill(Base):
    """Model de relação Usuário-Habilidade"""
    __tablename__ = "user_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    
    # Nível de proficiência
    level = Column(SQLEnum(SkillLevel), default=SkillLevel.BEGINNER, nullable=False)
    proficiency_score = Column(Float, default=0.0, nullable=False)  # 0-100
    
    # Metadados
    tasks_completed_count = Column(Integer, default=0, nullable=False)  # Tarefas usando essa skill
    last_used = Column(DateTime(timezone=True), nullable=True)  # Última vez que usou
    
    # Auto-atualização pela IA
    is_ai_detected = Column(Boolean, default=False, nullable=False)  # Detectada pela IA?
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relacionamentos
    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="user_skills")
    
    def __repr__(self):
        return f"<UserSkill(user_id={self.user_id}, skill='{self.skill.name}', level='{self.level}')>"
    
    @property
    def level_name(self) -> str:
        """Retorna nome amigável do nível"""
        level_names = {
            SkillLevel.BEGINNER: "Iniciante",
            SkillLevel.INTERMEDIATE: "Intermediário",
            SkillLevel.ADVANCED: "Avançado",
            SkillLevel.EXPERT: "Especialista"
        }
        return level_names.get(self.level, "Desconhecido")


# Import necessário
from sqlalchemy import Boolean
