"""
Rotas de Usuários - IdeiaTech
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.models.user import User, UserRole
from app.models.skill import UserSkill, Skill
from app.utils.jwt_handler import get_current_user, get_current_active_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# ============= SCHEMAS =============

class UserProfileResponse(BaseModel):
    """Schema para perfil completo do usuário"""
    id: int
    email: str
    username: str
    full_name: str
    role: str
    department: Optional[str]
    position: Optional[str]
    workload_capacity: int
    current_workload: int
    workload_percentage: float
    available_hours: int
    is_overloaded: bool
    
    class Config:
        from_attributes = True


class UserSkillResponse(BaseModel):
    """Schema para habilidade do usuário"""
    skill_name: str
    level: str
    proficiency_score: float
    tasks_completed_count: int
    is_ai_detected: bool


class TeamMemberSummary(BaseModel):
    """Schema para resumo de membro da equipe"""
    id: int
    full_name: str
    position: Optional[str]
    workload_percentage: float
    is_overloaded: bool
    skills_count: int


class UserUpdate(BaseModel):
    """Schema para atualização de usuário"""
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    workload_capacity: Optional[int] = Field(None, ge=1, le=168)


# ============= DEPENDENCY =============

def get_db():
    """Dependency de banco de dados"""
    pass


# ============= ENDPOINTS =============

@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Retorna perfil completo do usuário autenticado
    
    Inclui informações de workload e disponibilidade
    """
    return current_user


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza perfil do usuário autenticado
    
    Permite atualizar: nome completo, departamento, cargo, capacidade de trabalho
    """
    try:
        if profile_data.full_name:
            current_user.full_name = profile_data.full_name
        
        if profile_data.department:
            current_user.department = profile_data.department
        
        if profile_data.position:
            current_user.position = profile_data.position
        
        if profile_data.workload_capacity:
            current_user.workload_capacity = profile_data.workload_capacity
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Perfil atualizado: user_id={current_user.id}")
        
        return current_user
        
    except Exception as e:
        logger.error(f"Erro ao atualizar perfil: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar perfil"
        )


@router.get("/me/skills", response_model=List[UserSkillResponse])
async def get_my_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todas as habilidades do usuário autenticado
    
    Inclui skills manuais e detectadas pela IA
    """
    try:
        user_skills = db.query(UserSkill).filter(
            UserSkill.user_id == current_user.id
        ).join(Skill).all()
        
        skills_response = [
            {
                "skill_name": us.skill.name,
                "level": us.level.value,
                "proficiency_score": us.proficiency_score,
                "tasks_completed_count": us.tasks_completed_count,
                "is_ai_detected": us.is_ai_detected
            }
            for us in user_skills
        ]
        
        return skills_response
        
    except Exception as e:
        logger.error(f"Erro ao buscar skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar habilidades"
        )


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_manager),
    db: Session = Depends(get_db)
):
    """
    Busca usuário por ID (apenas gestores)
    
    Requer permissão de gestor
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Gestor só pode ver membros da sua equipe
        if current_user.role == UserRole.GESTOR:
            if user.manager_id != current_user.id and user.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Acesso negado: usuário não pertence à sua equipe"
                )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar usuário"
        )


@router.get("/team/members", response_model=List[TeamMemberSummary])
async def get_team_members(
    current_user: User = Depends(get_current_active_manager),
    db: Session = Depends(get_db),
    include_self: bool = Query(False, description="Incluir próprio gestor na lista")
):
    """
    Lista membros da equipe (apenas gestores)
    
    Retorna resumo de cada colaborador da equipe
    """
    try:
        query = db.query(User).filter(
            User.manager_id == current_user.id,
            User.is_active == True
        )
        
        team_members = query.all()
        
        members_summary = []
        
        for member in team_members:
            skills_count = db.query(UserSkill).filter(
                UserSkill.user_id == member.id
            ).count()
            
            members_summary.append({
                "id": member.id,
                "full_name": member.full_name,
                "position": member.position,
                "workload_percentage": member.workload_percentage,
                "is_overloaded": member.is_overloaded,
                "skills_count": skills_count
            })
        
        if include_self:
            skills_count = db.query(UserSkill).filter(
                UserSkill.user_id == current_user.id
            ).count()
            
            members_summary.insert(0, {
                "id": current_user.id,
                "full_name": current_user.full_name + " (Você)",
                "position": current_user.position,
                "workload_percentage": current_user.workload_percentage,
                "is_overloaded": current_user.is_overloaded,
                "skills_count": skills_count
            })
        
        return members_summary
        
    except Exception as e:
        logger.error(f"Erro ao listar equipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar membros da equipe"
        )


@router.post("/{user_id}/assign-manager")
async def assign_manager(
    user_id: int,
    manager_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atribui um gestor para o colaborador (apenas admins)
    
    Requer permissão de admin
    """
    try:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: apenas administradores"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        manager = db.query(User).filter(User.id == manager_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gestor não encontrado"
            )
        
        if manager.role not in [UserRole.GESTOR, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário especificado não é um gestor"
            )
        
        user.manager_id = manager_id
        db.commit()
        
        logger.info(f"Gestor atribuído: user_id={user_id}, manager_id={manager_id}")
        
        return {
            "message": "Gestor atribuído com sucesso",
            "user_id": user_id,
            "manager_id": manager_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atribuir gestor: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atribuir gestor"
        )
