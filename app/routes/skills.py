"""
Rotas de Habilidades - IdeiaTech
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.models.skill import Skill, UserSkill, SkillLevel
from app.models.user import User, UserRole
from app.utils.jwt_handler import get_current_user, get_current_active_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# ============= SCHEMAS =============

class SkillCreate(BaseModel):
    """Schema para criação de skill"""
    name: str = Field(..., min_length=2, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)


class SkillResponse(BaseModel):
    """Schema para resposta de skill"""
    id: int
    name: str
    category: Optional[str]
    description: Optional[str]
    
    class Config:
        from_attributes = True


class UserSkillAdd(BaseModel):
    """Schema para adicionar skill a usuário"""
    skill_id: int
    level: SkillLevel = SkillLevel.BEGINNER
    proficiency_score: float = Field(0.0, ge=0, le=100)


class UserSkillUpdate(BaseModel):
    """Schema para atualizar user skill"""
    level: Optional[SkillLevel] = None
    proficiency_score: Optional[float] = Field(None, ge=0, le=100)


class UserSkillResponse(BaseModel):
    """Schema para resposta de user skill"""
    id: int
    skill_id: int
    skill_name: str
    skill_category: Optional[str]
    level: str
    level_name: str
    proficiency_score: float
    tasks_completed_count: int
    is_ai_detected: bool
    
    class Config:
        from_attributes = True


# ============= DEPENDENCY =============

def get_db():
    """Dependency de banco de dados"""
    pass


# ============= ENDPOINTS - SKILLS GLOBAIS =============

@router.post("/", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    current_user: User = Depends(get_current_active_manager),
    db: Session = Depends(get_db)
):
    """
    Cria uma nova skill no sistema (apenas gestores)
    
    Skills criadas ficam disponíveis para todos os colaboradores
    """
    try:
        existing_skill = db.query(Skill).filter(
            Skill.name.ilike(skill_data.name)
        ).first()
        
        if existing_skill:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skill com este nome já existe"
            )
        
        new_skill = Skill(
            name=skill_data.name,
            category=skill_data.category,
            description=skill_data.description
        )
        
        db.add(new_skill)
        db.commit()
        db.refresh(new_skill)
        
        logger.info(f"Skill criada: skill_id={new_skill.id}, name={new_skill.name}")
        
        return new_skill
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar skill: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar skill"
        )


@router.get("/", response_model=List[SkillResponse])
async def list_all_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    search: Optional[str] = Query(None, description="Buscar por nome")
):
    """
    Lista todas as skills disponíveis no sistema
    
    Permite filtros por categoria e busca por nome
    """
    try:
        query = db.query(Skill)
        
        if category:
            query = query.filter(Skill.category.ilike(f"%{category}%"))
        
        if search:
            query = query.filter(Skill.name.ilike(f"%{search}%"))
        
        skills = query.order_by(Skill.name).all()
        
        return skills
        
    except Exception as e:
        logger.error(f"Erro ao listar skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar skills"
        )


@router.get("/categories")
async def list_skill_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todas as categorias de skills únicas
    """
    try:
        categories = db.query(Skill.category).distinct().filter(
            Skill.category.isnot(None)
        ).all()
        
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return {"categories": sorted(category_list)}
        
    except Exception as e:
        logger.error(f"Erro ao listar categorias: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar categorias"
        )


# ============= ENDPOINTS - USER SKILLS =============

@router.post("/user-skills", response_model=UserSkillResponse, status_code=status.HTTP_201_CREATED)
async def add_skill_to_user(
    user_skill_data: UserSkillAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None, description="ID do usuário (gestor pode especificar)")
):
    """
    Adiciona uma skill ao perfil do usuário
    
    Colaborador adiciona para si mesmo
    Gestor pode adicionar para membros da equipe
    """
    try:
        target_user_id = user_id if user_id else current_user.id
        
        if user_id and user_id != current_user.id:
            if current_user.role not in [UserRole.GESTOR, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Apenas gestores podem adicionar skills para outros usuários"
                )
            
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado"
                )
            
            if current_user.role == UserRole.GESTOR:
                if target_user.manager_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Usuário não pertence à sua equipe"
                    )
        
        skill = db.query(Skill).filter(Skill.id == user_skill_data.skill_id).first()
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill não encontrada"
            )
        
        existing = db.query(UserSkill).filter(
            UserSkill.user_id == target_user_id,
            UserSkill.skill_id == user_skill_data.skill_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário já possui esta skill"
            )
        
        new_user_skill = UserSkill(
            user_id=target_user_id,
            skill_id=user_skill_data.skill_id,
            level=user_skill_data.level,
            proficiency_score=user_skill_data.proficiency_score,
            is_ai_detected=False
        )
        
        db.add(new_user_skill)
        db.commit()
        db.refresh(new_user_skill)
        
        logger.info(f"Skill adicionada: user_id={target_user_id}, skill_id={user_skill_data.skill_id}")
        
        response = {
            "id": new_user_skill.id,
            "skill_id": new_user_skill.skill_id,
            "skill_name": skill.name,
            "skill_category": skill.category,
            "level": new_user_skill.level.value,
            "level_name": new_user_skill.level_name,
            "proficiency_score": new_user_skill.proficiency_score,
            "tasks_completed_count": new_user_skill.tasks_completed_count,
            "is_ai_detected": new_user_skill.is_ai_detected
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao adicionar skill: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao adicionar skill"
        )


@router.get("/user-skills/me", response_model=List[UserSkillResponse])
async def get_my_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista skills do usuário autenticado
    """
    try:
        user_skills = db.query(UserSkill).filter(
            UserSkill.user_id == current_user.id
        ).join(Skill).all()
        
        skills_response = []
        for us in user_skills:
            skills_response.append({
                "id": us.id,
                "skill_id": us.skill_id,
                "skill_name": us.skill.name,
                "skill_category": us.skill.category,
                "level": us.level.value,
                "level_name": us.level_name,
                "proficiency_score": us.proficiency_score,
                "tasks_completed_count": us.tasks_completed_count,
                "is_ai_detected": us.is_ai_detected
            })
        
        return skills_response
        
    except Exception as e:
        logger.error(f"Erro ao buscar skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar skills"
        )


@router.get("/user-skills/{user_id}", response_model=List[UserSkillResponse])
async def get_user_skills(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista skills de um usuário específico
    
    Colaborador pode ver apenas próprias skills
    Gestor pode ver skills da equipe
    """
    try:
        if user_id != current_user.id:
            if current_user.role not in [UserRole.GESTOR, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sem permissão para ver skills de outros usuários"
                )
            
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado"
                )
            
            if current_user.role == UserRole.GESTOR:
                if target_user.manager_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Usuário não pertence à sua equipe"
                    )
        
        user_skills = db.query(UserSkill).filter(
            UserSkill.user_id == user_id
        ).join(Skill).all()
        
        skills_response = []
        for us in user_skills:
            skills_response.append({
                "id": us.id,
                "skill_id": us.skill_id,
                "skill_name": us.skill.name,
                "skill_category": us.skill.category,
                "level": us.level.value,
                "level_name": us.level_name,
                "proficiency_score": us.proficiency_score,
                "tasks_completed_count": us.tasks_completed_count,
                "is_ai_detected": us.is_ai_detected
            })
        
        return skills_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar skills do usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar skills"
        )


@router.put("/user-skills/{user_skill_id}", response_model=UserSkillResponse)
async def update_user_skill(
    user_skill_id: int,
    update_data: UserSkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza nível e proficiência de uma skill do usuário
    
    Colaborador não pode editar próprias skills (apenas visualizar)
    Apenas gestor pode atualizar
    """
    try:
        user_skill = db.query(UserSkill).filter(UserSkill.id == user_skill_id).first()
        
        if not user_skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill do usuário não encontrada"
            )
        
        if current_user.role not in [UserRole.GESTOR, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas gestores podem editar skills"
            )
        
        target_user = db.query(User).filter(User.id == user_skill.user_id).first()
        
        if current_user.role == UserRole.GESTOR:
            if target_user.manager_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Usuário não pertence à sua equipe"
                )
        
        if update_data.level:
            user_skill.level = update_data.level
        
        if update_data.proficiency_score is not None:
            user_skill.proficiency_score = update_data.proficiency_score
        
        db.commit()
        db.refresh(user_skill)
        
        logger.info(f"Skill atualizada: user_skill_id={user_skill_id}")
        
        response = {
            "id": user_skill.id,
            "skill_id": user_skill.skill_id,
            "skill_name": user_skill.skill.name,
            "skill_category": user_skill.skill.category,
            "level": user_skill.level.value,
            "level_name": user_skill.level_name,
            "proficiency_score": user_skill.proficiency_score,
            "tasks_completed_count": user_skill.tasks_completed_count,
            "is_ai_detected": user_skill.is_ai_detected
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar skill: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar skill"
        )


@router.delete("/user-skills/{user_skill_id}")
async def delete_user_skill(
    user_skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove uma skill do perfil do usuário
    
    Colaborador pode remover próprias skills
    Gestor pode remover skills da equipe
    """
    try:
        user_skill = db.query(UserSkill).filter(UserSkill.id == user_skill_id).first()
        
        if not user_skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill do usuário não encontrada"
            )
        
        if user_skill.user_id != current_user.id:
            if current_user.role not in [UserRole.GESTOR, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sem permissão para remover esta skill"
                )
            
            target_user = db.query(User).filter(User.id == user_skill.user_id).first()
            
            if current_user.role == UserRole.GESTOR:
                if target_user.manager_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Usuário não pertence à sua equipe"
                    )
        
        db.delete(user_skill)
        db.commit()
        
        logger.info(f"Skill removida: user_skill_id={user_skill_id}")
        
        return {"message": "Skill removida com sucesso", "user_skill_id": user_skill_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover skill: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao remover skill"
        )
