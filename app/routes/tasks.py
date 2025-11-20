"""
Rotas de Tarefas - IdeiaTech
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging
import json

from app.models.task import Task, TaskStatus, TaskPriority
from app.models.user import User, UserRole
from app.utils.jwt_handler import get_current_user, get_current_active_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# ============= SCHEMAS =============

class TaskCreate(BaseModel):
    """Schema para criação de tarefa"""
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_hours: Optional[float] = Field(None, ge=0.5, le=200)
    required_skills: Optional[List[str]] = []
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None


class TaskUpdate(BaseModel):
    """Schema para atualização de tarefa"""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    estimated_hours: Optional[float] = Field(None, ge=0.5, le=200)
    actual_hours: Optional[float] = Field(None, ge=0)
    assigned_to: Optional[int] = None


class TaskResponse(BaseModel):
    """Schema para resposta de tarefa"""
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    estimated_hours: Optional[float]
    actual_hours: float
    progress_percentage: float
    is_overdue: bool
    assigned_to: Optional[int]
    assigned_user_name: Optional[str]
    created_by: int
    creator_name: str
    ai_match_score: Optional[float]
    ai_recommendation_reason: Optional[str]
    due_date: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= DEPENDENCY =============

def get_db():
    """Dependency de banco de dados"""
    pass


# ============= ENDPOINTS =============

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_manager),
    db: Session = Depends(get_db)
):
    """
    Cria uma nova tarefa (apenas gestores)
    
    Permite atribuição opcional no momento da criação
    """
    try:
        # Converte skills para JSON
        required_skills_json = None
        if task_data.required_skills:
            required_skills_json = json.dumps(task_data.required_skills, ensure_ascii=False)
        
        # Valida usuário atribuído
        if task_data.assigned_to:
            assigned_user = db.query(User).filter(User.id == task_data.assigned_to).first()
            if not assigned_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário para atribuição não encontrado"
                )
            
            # Verifica se é da equipe
            if current_user.role == UserRole.GESTOR:
                if assigned_user.manager_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Você só pode atribuir tarefas para membros da sua equipe"
                    )
        
        # Cria tarefa
        new_task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            estimated_hours=task_data.estimated_hours,
            required_skills=required_skills_json,
            due_date=task_data.due_date,
            assigned_to=task_data.assigned_to,
            created_by=current_user.id,
            status=TaskStatus.PENDING
        )
        
        db.add(new_task)
        
        # Atualiza workload se atribuída
        if task_data.assigned_to and task_data.estimated_hours:
            assigned_user = db.query(User).filter(User.id == task_data.assigned_to).first()
            if assigned_user:
                assigned_user.current_workload += task_data.estimated_hours
        
        db.commit()
        db.refresh(new_task)
        
        logger.info(f"Tarefa criada: task_id={new_task.id}, created_by={current_user.id}")
        
        # Prepara resposta
        response = {
            **new_task.__dict__,
            "status": new_task.status.value,
            "priority": new_task.priority.value,
            "assigned_user_name": new_task.assigned_user.full_name if new_task.assigned_user else None,
            "creator_name": new_task.creator.full_name
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar tarefa: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar tarefa"
        )


@router.get("/my-tasks", response_model=List[TaskResponse])
async def get_my_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: Optional[TaskStatus] = Query(None, description="Filtrar por status"),
    priority_filter: Optional[TaskPriority] = Query(None, description="Filtrar por prioridade")
):
    """
    Lista tarefas atribuídas ao usuário autenticado
    
    Permite filtros por status e prioridade
    """
    try:
        query = db.query(Task).filter(Task.assigned_to == current_user.id)
        
        if status_filter:
            query = query.filter(Task.status == status_filter)
        
        if priority_filter:
            query = query.filter(Task.priority == priority_filter)
        
        tasks = query.order_by(Task.created_at.desc()).all()
        
        tasks_response = []
        for task in tasks:
            tasks_response.append({
                **task.__dict__,
                "status": task.status.value,
                "priority": task.priority.value,
                "assigned_user_name": current_user.full_name,
                "creator_name": task.creator.full_name if task.creator else "Sistema"
            })
        
        return tasks_response
        
    except Exception as e:
        logger.error(f"Erro ao listar tarefas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar tarefas"
        )


@router.get("/team-tasks", response_model=List[TaskResponse])
async def get_team_tasks(
    current_user: User = Depends(get_current_active_manager),
    db: Session = Depends(get_db),
    status_filter: Optional[TaskStatus] = Query(None, description="Filtrar por status"),
    assigned_to: Optional[int] = Query(None, description="Filtrar por colaborador")
):
    """
    Lista tarefas da equipe (apenas gestores)
    
    Permite filtros por status e colaborador
    """
    try:
        # Busca membros da equipe
        team_member_ids = [m.id for m in db.query(User).filter(
            User.manager_id == current_user.id
        ).all()]
        
        query = db.query(Task).filter(Task.assigned_to.in_(team_member_ids))
        
        if status_filter:
            query = query.filter(Task.status == status_filter)
        
        if assigned_to:
            if assigned_to not in team_member_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Colaborador não pertence à sua equipe"
                )
            query = query.filter(Task.assigned_to == assigned_to)
        
        tasks = query.order_by(Task.created_at.desc()).all()
        
        tasks_response = []
        for task in tasks:
            tasks_response.append({
                **task.__dict__,
                "status": task.status.value,
                "priority": task.priority.value,
                "assigned_user_name": task.assigned_user.full_name if task.assigned_user else None,
                "creator_name": task.creator.full_name if task.creator else "Sistema"
            })
        
        return tasks_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar tarefas da equipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar tarefas da equipe"
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Busca tarefa por ID
    
    Usuário deve ser o atribuído, criador, ou gestor
    """
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarefa não encontrada"
            )
        
        # Verifica permissão
        is_assigned = task.assigned_to == current_user.id
        is_creator = task.created_by == current_user.id
        is_manager = current_user.role in [UserRole.GESTOR, UserRole.ADMIN]
        
        if not (is_assigned or is_creator or is_manager):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado a esta tarefa"
            )
        
        response = {
            **task.__dict__,
            "status": task.status.value,
            "priority": task.priority.value,
            "assigned_user_name": task.assigned_user.full_name if task.assigned_user else None,
            "creator_name": task.creator.full_name if task.creator else "Sistema"
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar tarefa: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar tarefa"
        )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza uma tarefa
    
    Colaborador pode atualizar status e horas reais
    Gestor pode atualizar todos os campos
    """
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarefa não encontrada"
            )
        
        is_assigned = task.assigned_to == current_user.id
        is_manager = current_user.role in [UserRole.GESTOR, UserRole.ADMIN]
        
        if not (is_assigned or is_manager):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para atualizar esta tarefa"
            )
        
        # Colaborador só pode atualizar status e horas
        if is_assigned and not is_manager:
            if task_data.status:
                task.status = task_data.status
            if task_data.actual_hours is not None:
                task.actual_hours = task_data.actual_hours
        
        # Gestor pode atualizar tudo
        if is_manager:
            if task_data.title:
                task.title = task_data.title
            if task_data.description is not None:
                task.description = task_data.description
            if task_data.status:
                task.status = task_data.status
            if task_data.priority:
                task.priority = task_data.priority
            if task_data.estimated_hours is not None:
                task.estimated_hours = task_data.estimated_hours
            if task_data.actual_hours is not None:
                task.actual_hours = task_data.actual_hours
            if task_data.assigned_to is not None:
                task.assigned_to = task_data.assigned_to
        
        # Marca timestamps
        if task_data.status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = datetime.now()
        
        if task_data.status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.now()
        
        db.commit()
        db.refresh(task)
        
        logger.info(f"Tarefa atualizada: task_id={task_id}, user_id={current_user.id}")
        
        response = {
            **task.__dict__,
            "status": task.status.value,
            "priority": task.priority.value,
            "assigned_user_name": task.assigned_user.full_name if task.assigned_user else None,
            "creator_name": task.creator.full_name if task.creator else "Sistema"
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar tarefa: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar tarefa"
        )


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_manager),
    db: Session = Depends(get_db)
):
    """
    Deleta uma tarefa (apenas gestores)
    
    Remove a tarefa e ajusta workload do usuário atribuído
    """
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarefa não encontrada"
            )
        
        # Ajusta workload se houver usuário atribuído
        if task.assigned_to and task.estimated_hours:
            assigned_user = db.query(User).filter(User.id == task.assigned_to).first()
            if assigned_user:
                assigned_user.current_workload = max(
                    0,
                    assigned_user.current_workload - task.estimated_hours
                )
        
        db.delete(task)
        db.commit()
        
        logger.info(f"Tarefa deletada: task_id={task_id}, deleted_by={current_user.id}")
        
        return {"message": "Tarefa deletada com sucesso", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar tarefa: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao deletar tarefa"
        )
