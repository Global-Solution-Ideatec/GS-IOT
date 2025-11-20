"""
Rotas de IA e Recomendações - IdeiaTech
Integração com Gemini AI para recomendações inteligentes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.models.user import User, UserRole
from app.models.task import Task
from app.models.wellbeing import WellbeingCheck, MoodLevel, EnergyLevel
from app.utils.jwt_handler import get_current_user, get_current_active_manager
from app.services.gemini_service import gemini_service
from app.services.task_distribution import TaskDistributionService
from app.services.sentiment_analysis import SentimentAnalysisService

logger = logging.getLogger(__name__)
router = APIRouter()


# ============= SCHEMAS =============

class WellbeingCheckCreate(BaseModel):
    """Schema para criar check-in de bem-estar"""
    mood: MoodLevel
    energy: EnergyLevel
    notes: Optional[str] = Field(None, max_length=500)


class WellbeingCheckResponse(BaseModel):
    """Schema para resposta de check-in"""
    id: int
    mood: str
    mood_emoji: str
    energy: str
    energy_bars: str
    notes: Optional[str]
    ai_sentiment_score: Optional[int]
    ai_burnout_risk: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TaskRecommendationRequest(BaseModel):
    """Schema para solicitar recomendação de tarefa"""
    task_id: int
    auto_assign: bool = Field(False, description="Atribuir automaticamente ao recomendado")


class DevelopmentPlanRequest(BaseModel):
    """Schema para solicitar plano de desenvolvimento"""
    target_role: Optional[str] = None


# ============= DEPENDENCY =============

def get_db():
    """Dependency de banco de dados"""
    pass


# ============= ENDPOINTS - BEM-ESTAR =============

@router.post("/wellbeing/check-in", response_model=WellbeingCheckResponse, status_code=status.HTTP_201_CREATED)
async def create_wellbeing_check(
    check_data: WellbeingCheckCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registra check-in de bem-estar do colaborador
    
    IA analisa automaticamente o check-in e gera insights
    """
    try:
        new_check = WellbeingCheck(
            user_id=current_user.id,
            mood=check_data.mood,
            energy=check_data.energy,
            notes=check_data.notes
        )
        
        db.add(new_check)
        db.commit()
        db.refresh(new_check)
        
        logger.info(f"Check-in registrado: user_id={current_user.id}, mood={check_data.mood.value}")
        
        sentiment_service = SentimentAnalysisService(db)
        analysis = sentiment_service.analyze_user_wellbeing(current_user.id, days=30)
        
        if "sentiment_score" in analysis:
            new_check.ai_sentiment_score = analysis.get("sentiment_score")
            new_check.ai_burnout_risk = analysis.get("burnout_risk")
            db.commit()
            db.refresh(new_check)
        
        response = {
            "id": new_check.id,
            "mood": new_check.mood.value,
            "mood_emoji": new_check.mood_emoji,
            "energy": new_check.energy.value,
            "energy_bars": new_check.energy_bars,
            "notes": new_check.notes,
            "ai_sentiment_score": new_check.ai_sentiment_score,
            "ai_burnout_risk": new_check.ai_burnout_risk,
            "created_at": new_check.created_at
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao criar check-in: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao registrar check-in"
        )


@router.get("/wellbeing/my-analysis")
async def get_my_wellbeing_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=7, le=90, description="Período de análise em dias")
):
    """
    Análise completa de bem-estar do usuário autenticado
    
    Retorna tendências, scores e recomendações personalizadas da IA
    """
    try:
        sentiment_service = SentimentAnalysisService(db)
        analysis = sentiment_service.analyze_user_wellbeing(current_user.id, days=days)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Erro na análise de bem-estar: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao analisar bem-estar"
        )


@router.get("/wellbeing/my-history", response_model=List[WellbeingCheckResponse])
async def get_my_wellbeing_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=7, le=90, description="Período em dias")
):
    """
    Histórico de check-ins de bem-estar do usuário
    """
    try:
        since_date = datetime.now() - timedelta(days=days)
        
        checks = db.query(WellbeingCheck).filter(
            WellbeingCheck.user_id == current_user.id,
            WellbeingCheck.created_at >= since_date
        ).order_by(WellbeingCheck.created_at.desc()).all()
        
        checks_response = []
        for check in checks:
            checks_response.append({
                "id": check.id,
                "mood": check.mood.value,
                "mood_emoji": check.mood_emoji,
                "energy": check.energy.value,
                "energy_bars": check.energy_bars,
                "notes": check.notes,
                "ai_sentiment_score": check.ai_sentiment_score,
                "ai_burnout_risk": check.ai_burnout_risk,
                "created_at": check.created_at
            })
        
        return checks_response
        
    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar histórico"
        )


@router.get("/wellbeing/team-summary")
async def get_team_wellbeing_summary(
    current_user: User = Depends(get_current_active_manager),
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=30, description="Período em dias")
):
    """
    Resumo de bem-estar da equipe (apenas gestores)
    
    Mostra status geral, alertas e membros que precisam de atenção
    """
    try:
        sentiment_service = SentimentAnalysisService(db)
        summary = sentiment_service.get_team_wellbeing_summary(current_user.id, days=days)
        
        return summary
        
    except Exception as e:
        logger.error(f"Erro no resumo da equipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao gerar resumo da equipe"
        )


# ============= ENDPOINTS - RECOMENDAÇÕES DE TAREFAS =============

@router.post("/tasks/recommend")
async def recommend_task_assignment(
    request: TaskRecommendationRequest,
    current_user: User = Depends(get_current_active_manager),
    db: Session = Depends(get_db)
):
    """
    Recomenda colaborador ideal para uma tarefa usando IA (apenas gestores)
    
    Analisa skills, carga de trabalho e bem-estar para fazer match inteligente
    Pode atribuir automaticamente se especificado
    """
    try:
        task_service = TaskDistributionService(db)
        
        if request.auto_assign:
            result = task_service.auto_distribute_task(
                task_id=request.task_id,
                auto_assign=True
            )
        else:
            result = task_service.recommend_assignee(
                task_id=request.task_id,
                team_id=current_user.id
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Erro na recomendação de tarefa: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao recomendar atribuição"
        )


@router.post("/tasks/rebalance-team")
async def rebalance_team_workload(
    current_user: User = Depends(get_current_active_manager),
    db: Session = Depends(get_db),
    dry_run: bool = Query(True, description="Simular sem aplicar mudanças"),
    apply: bool = Query(False, description="Aplicar rebalanceamento")
):
    """
    Rebalanceia carga de trabalho da equipe usando IA (apenas gestores)
    
    Identifica sobrecargas e sugere redistribuição inteligente
    dry_run=True apenas simula, apply=True aplica as mudanças
    """
    try:
        task_service = TaskDistributionService(db)
        result = task_service.rebalance_team_workload(
            team_id=current_user.id,
            dry_run=not apply
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Erro no rebalanceamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao rebalancear equipe"
        )


# ============= ENDPOINTS - DESENVOLVIMENTO =============

@router.post("/development/skill-plan")
async def generate_skill_development_plan(
    request: DevelopmentPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Gera plano personalizado de desenvolvimento de habilidades usando IA
    
    Analisa skills atuais e sugere cursos, práticas e próximos passos
    """
    try:
        from app.models.skill import UserSkill, Skill
        
        user_skills = db.query(UserSkill).filter(
            UserSkill.user_id == current_user.id
        ).join(Skill).all()
        
        user_profile = {
            "name": current_user.full_name,
            "position": current_user.position,
            "department": current_user.department
        }
        
        current_skills = [
            {
                "name": us.skill.name,
                "level": us.level.value,
                "proficiency_score": us.proficiency_score,
                "category": us.skill.category
            }
            for us in user_skills
        ]
        
        plan = gemini_service.generate_skill_development_plan(
            user_profile=user_profile,
            current_skills=current_skills,
            target_role=request.target_role
        )
        
        return plan
        
    except Exception as e:
        logger.error(f"Erro ao gerar plano de desenvolvimento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao gerar plano de desenvolvimento"
        )


# ============= ENDPOINTS - INSIGHTS GERENCIAIS =============

@router.get("/insights/team")
async def get_team_insights(
    current_user: User = Depends(get_current_active_manager),
    db: Session = Depends(get_db),
    period: str = Query("week", regex="^(week|month)$", description="Período de análise")
):
    """
    Insights e recomendações sobre a equipe usando IA (apenas gestores)
    
    Dashboard executivo com métricas, alertas e ações sugeridas
    """
    try:
        from app.models.skill import UserSkill
        
        team_members = db.query(User).filter(
            User.manager_id == current_user.id,
            User.is_active == True
        ).all()
        
        days = 7 if period == "week" else 30
        since_date = datetime.now() - timedelta(days=days)
        
        team_data = {
            "period": period,
            "team_size": len(team_members),
            "members": []
        }
        
        for member in team_members:
            tasks_count = db.query(Task).filter(
                Task.assigned_to == member.id,
                Task.updated_at >= since_date
            ).count()
            
            completed_tasks = db.query(Task).filter(
                Task.assigned_to == member.id,
                Task.status == "completed",
                Task.completed_at >= since_date
            ).count()
            
            skills_count = db.query(UserSkill).filter(
                UserSkill.user_id == member.id
            ).count()
            
            last_check = db.query(WellbeingCheck).filter(
                WellbeingCheck.user_id == member.id,
                WellbeingCheck.created_at >= since_date
            ).order_by(WellbeingCheck.created_at.desc()).first()
            
            team_data["members"].append({
                "name": member.full_name,
                "position": member.position,
                "workload_percentage": member.workload_percentage,
                "tasks_assigned": tasks_count,
                "tasks_completed": completed_tasks,
                "skills_count": skills_count,
                "last_mood": last_check.mood.value if last_check else None,
                "last_energy": last_check.energy.value if last_check else None,
                "burnout_risk": last_check.ai_burnout_risk if last_check else None
            })
        
        insights = gemini_service.generate_team_insights(
            team_data=team_data,
            time_period=period
        )
        
        return insights
        
    except Exception as e:
        logger.error(f"Erro ao gerar insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao gerar insights da equipe"
        )
