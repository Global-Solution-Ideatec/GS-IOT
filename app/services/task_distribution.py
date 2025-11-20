"""
Task Distribution Service - IdeiaTech
Sistema inteligente de distribuição de tarefas
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole
from app.models.skill import UserSkill, Skill
from app.models.wellbeing import WellbeingCheck
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class TaskDistributionService:
    """Serviço de distribuição inteligente de tarefas"""
    
    def __init__(self, db: Session):
        self.db = db
    
    
    def recommend_assignee(
        self,
        task_id: int,
        team_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Recomenda quem deve receber a tarefa
        
        Args:
            task_id: ID da tarefa
            team_id: ID do gestor/equipe (opcional)
        
        Returns:
            Recomendação com score e justificativa
        """
        try:
            # Busca a tarefa
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return {"error": "Tarefa não encontrada"}
            
            # Busca candidatos elegíveis
            candidates = self._get_eligible_candidates(task, team_id)
            
            if not candidates:
                return {"error": "Nenhum colaborador disponível"}
            
            # Prepara dados para a IA
            task_data = self._prepare_task_data(task)
            candidates_data = [self._prepare_candidate_data(c) for c in candidates]
            team_context = self._get_team_context(team_id)
            
            # Chama a IA para recomendação
            logger.info(f"Solicitando recomendação da IA para tarefa #{task_id}")
            recommendation = gemini_service.generate_task_recommendation(
                task=task_data,
                candidates=candidates_data,
                team_context=team_context
            )
            
            # Enriquece a recomendação com dados locais
            if "recommended_user_id" in recommendation:
                user = self.db.query(User).filter(
                    User.id == recommendation["recommended_user_id"]
                ).first()
                
                if user:
                    recommendation["user_details"] = {
                        "email": user.email,
                        "position": user.position,
                        "department": user.department
                    }
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Erro na recomendação: {str(e)}")
            return {"error": str(e)}
    
    
    def auto_distribute_task(
        self,
        task_id: int,
        auto_assign: bool = False
    ) -> Dict[str, Any]:
        """
        Distribui automaticamente a tarefa
        
        Args:
            task_id: ID da tarefa
            auto_assign: Se True, atribui automaticamente ao recomendado
        
        Returns:
            Resultado da distribuição
        """
        try:
            recommendation = self.recommend_assignee(task_id)
            
            if "error" in recommendation:
                return recommendation
            
            if auto_assign and "recommended_user_id" in recommendation:
                task = self.db.query(Task).filter(Task.id == task_id).first()
                user_id = recommendation["recommended_user_id"]
                
                # Atribui a tarefa
                task.assigned_to = user_id
                task.status = TaskStatus.PENDING
                task.ai_match_score = recommendation.get("match_score", 0)
                task.ai_recommendation_reason = recommendation.get("reasoning", "")
                
                # Atualiza workload do usuário
                user = self.db.query(User).filter(User.id == user_id).first()
                if user and task.estimated_hours:
                    user.current_workload += task.estimated_hours
                
                self.db.commit()
                
                logger.info(f"Tarefa #{task_id} atribuída automaticamente para user #{user_id}")
                
                recommendation["assigned"] = True
                recommendation["message"] = "Tarefa atribuída com sucesso"
            
            return recommendation
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro na distribuição: {str(e)}")
            return {"error": str(e)}
    
    
    def rebalance_team_workload(
        self,
        team_id: int,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Rebalanceia a carga de trabalho da equipe
        
        Args:
            team_id: ID do gestor
            dry_run: Se True, apenas simula sem aplicar mudanças
        
        Returns:
            Relatório de rebalanceamento
        """
        try:
            # Busca membros da equipe
            team_members = self.db.query(User).filter(
                User.manager_id == team_id,
                User.is_active == True
            ).all()
            
            if not team_members:
                return {"error": "Equipe não encontrada"}
            
            # Identifica sobrecargas
            overloaded = [u for u in team_members if u.is_overloaded]
            underloaded = [u for u in team_members if u.workload_percentage < 70]
            
            recommendations = []
            
            for overloaded_user in overloaded:
                # Busca tarefas pendentes do usuário sobrecarregado
                pending_tasks = self.db.query(Task).filter(
                    Task.assigned_to == overloaded_user.id,
                    Task.status == TaskStatus.PENDING
                ).order_by(Task.priority.desc()).all()
                
                for task in pending_tasks[:3]:  # Top 3 tarefas
                    # Recomenda redistribuição
                    rec = self.recommend_assignee(task.id, team_id)
                    
                    if "recommended_user_id" in rec:
                        if rec["recommended_user_id"] != overloaded_user.id:
                            recommendations.append({
                                "task_id": task.id,
                                "task_title": task.title,
                                "from_user": overloaded_user.username,
                                "to_user": rec.get("recommended_user_name"),
                                "to_user_id": rec["recommended_user_id"],
                                "reason": rec.get("reasoning"),
                                "match_score": rec.get("match_score")
                            })
            
            # Aplica mudanças se não for dry_run
            if not dry_run and recommendations:
                for rec in recommendations:
                    task = self.db.query(Task).filter(Task.id == rec["task_id"]).first()
                    old_user = self.db.query(User).filter(
                        User.username == rec["from_user"]
                    ).first()
                    new_user = self.db.query(User).filter(
                        User.id == rec["to_user_id"]
                    ).first()
                    
                    if task and old_user and new_user:
                        # Atualiza atribuição
                        task.assigned_to = new_user.id
                        
                        # Ajusta workloads
                        if task.estimated_hours:
                            old_user.current_workload -= task.estimated_hours
                            new_user.current_workload += task.estimated_hours
                
                self.db.commit()
                logger.info(f"Rebalanceamento aplicado: {len(recommendations)} tarefas redistribuídas")
            
            return {
                "overloaded_count": len(overloaded),
                "underloaded_count": len(underloaded),
                "recommendations": recommendations,
                "applied": not dry_run,
                "summary": f"{len(recommendations)} tarefas recomendadas para redistribuição"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro no rebalanceamento: {str(e)}")
            return {"error": str(e)}
    
    
    # ============= HELPERS =============
    
    def _get_eligible_candidates(
        self,
        task: Task,
        team_id: Optional[int]
    ) -> List[User]:
        """Busca colaboradores elegíveis para a tarefa"""
        query = self.db.query(User).filter(
            User.role == UserRole.COLABORADOR,
            User.is_active == True
        )
        
        # Filtra por equipe se especificado
        if team_id:
            query = query.filter(User.manager_id == team_id)
        
        # Filtra por disponibilidade mínima
        candidates = [u for u in query.all() if u.available_hours > 0]
        
        return candidates
    
    
    def _prepare_task_data(self, task: Task) -> Dict[str, Any]:
        """Prepara dados da tarefa para a IA"""
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority.value,
            "estimated_hours": task.estimated_hours or 0,
            "required_skills": self._parse_required_skills(task.required_skills),
            "due_date": str(task.due_date) if task.due_date else None
        }
    
    
    def _prepare_candidate_data(self, user: User) -> Dict[str, Any]:
        """Prepara dados do candidato para a IA"""
        # Busca skills do usuário
        user_skills = self.db.query(UserSkill).filter(
            UserSkill.user_id == user.id
        ).join(Skill).all()
        
        skills = [us.skill.name for us in user_skills]
        
        # Busca último check-in de bem-estar
        last_wellbeing = self.db.query(WellbeingCheck).filter(
            WellbeingCheck.user_id == user.id
        ).order_by(WellbeingCheck.created_at.desc()).first()
        
        return {
            "id": user.id,
            "name": user.full_name,
            "username": user.username,
            "position": user.position,
            "skills": skills,
            "workload": round(user.workload_percentage, 1),
            "available_hours": user.available_hours,
            "energy": last_wellbeing.energy.value if last_wellbeing else "medium",
            "mood": last_wellbeing.mood.value if last_wellbeing else "neutral"
        }
    
    
    def _get_team_context(self, team_id: Optional[int]) -> Optional[Dict[str, Any]]:
        """Busca contexto da equipe"""
        if not team_id:
            return None
        
        team_members = self.db.query(User).filter(
            User.manager_id == team_id
        ).all()
        
        if not team_members:
            return None
        
        return {
            "team_size": len(team_members),
            "average_workload": sum(u.workload_percentage for u in team_members) / len(team_members),
            "overloaded_count": sum(1 for u in team_members if u.is_overloaded)
        }
    
    
    def _parse_required_skills(self, skills_json: Optional[str]) -> List[str]:
        """Parse skills do JSON"""
        if not skills_json:
            return []
        
        try:
            import json
            return json.loads(skills_json)
        except:
            return []
