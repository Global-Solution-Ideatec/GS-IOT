"""
Sentiment Analysis Service - IdeiaTech
Análise de sentimentos e bem-estar dos colaboradores
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import Counter
import logging

from app.models.user import User
from app.models.wellbeing import WellbeingCheck, MoodLevel, EnergyLevel
from app.models.task import Task, TaskStatus
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class SentimentAnalysisService:
    """Serviço de análise de sentimentos e bem-estar"""
    
    def __init__(self, db: Session):
        self.db = db
    
    
    def analyze_user_wellbeing(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analisa bem-estar do usuário em período específico
        
        Args:
            user_id: ID do usuário
            days: Número de dias para análise
        
        Returns:
            Análise completa com scores e tendências
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "Usuário não encontrado"}
            
            # Busca histórico de bem-estar
            since_date = datetime.now() - timedelta(days=days)
            wellbeing_history = self.db.query(WellbeingCheck).filter(
                WellbeingCheck.user_id == user_id,
                WellbeingCheck.created_at >= since_date
            ).order_by(WellbeingCheck.created_at.desc()).all()
            
            if not wellbeing_history:
                return {
                    "user_id": user_id,
                    "user_name": user.full_name,
                    "message": "Sem dados de bem-estar disponíveis",
                    "recommendation": "Incentive check-ins regulares"
                }
            
            # Busca tarefas recentes
            recent_tasks = self.db.query(Task).filter(
                Task.assigned_to == user_id,
                Task.updated_at >= since_date
            ).all()
            
            # Análise local
            local_analysis = self._calculate_local_metrics(wellbeing_history)
            
            # Prepara dados para IA
            wellbeing_data = [self._prepare_wellbeing_data(w) for w in wellbeing_history]
            tasks_data = [self._prepare_task_data(t) for t in recent_tasks]
            
            # Solicita análise da IA
            logger.info(f"Solicitando análise de bem-estar para user #{user_id}")
            ai_analysis = gemini_service.analyze_wellbeing_trend(
                user_name=user.full_name,
                wellbeing_history=wellbeing_data,
                recent_tasks=tasks_data
            )
            
            # Combina análises
            combined_analysis = {
                **local_analysis,
                **ai_analysis,
                "user_id": user_id,
                "user_name": user.full_name,
                "period_days": days,
                "check_ins_count": len(wellbeing_history),
                "analyzed_at": datetime.now().isoformat()
            }
            
            # Salva insights no último check-in
            if wellbeing_history and "sentiment_score" in ai_analysis:
                latest_check = wellbeing_history[0]
                latest_check.ai_sentiment_score = ai_analysis.get("sentiment_score")
                latest_check.ai_burnout_risk = ai_analysis.get("burnout_risk")
                
                import json
                if "recommendations" in ai_analysis:
                    latest_check.ai_recommendations = json.dumps(
                        ai_analysis["recommendations"],
                        ensure_ascii=False
                    )
                
                self.db.commit()
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Erro na análise de bem-estar: {str(e)}")
            return {"error": str(e)}
    
    
    def get_team_wellbeing_summary(
        self,
        team_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Resumo de bem-estar da equipe para o gestor
        
        Args:
            team_id: ID do gestor
            days: Número de dias para análise
        
        Returns:
            Resumo da equipe com alertas
        """
        try:
            # Busca membros da equipe
            team_members = self.db.query(User).filter(
                User.manager_id == team_id,
                User.is_active == True
            ).all()
            
            if not team_members:
                return {"error": "Equipe não encontrada"}
            
            since_date = datetime.now() - timedelta(days=days)
            
            team_summary = {
                "team_size": len(team_members),
                "period_days": days,
                "members_analysis": [],
                "alerts": [],
                "average_scores": {},
                "trend": "stable"
            }
            
            mood_scores = []
            energy_scores = []
            burnout_risks = []
            
            for member in team_members:
                # Último check-in do membro
                last_check = self.db.query(WellbeingCheck).filter(
                    WellbeingCheck.user_id == member.id,
                    WellbeingCheck.created_at >= since_date
                ).order_by(WellbeingCheck.created_at.desc()).first()
                
                if last_check:
                    mood_score = self._mood_to_score(last_check.mood)
                    energy_score = self._energy_to_score(last_check.energy)
                    
                    mood_scores.append(mood_score)
                    energy_scores.append(energy_score)
                    
                    member_data = {
                        "user_id": member.id,
                        "name": member.full_name,
                        "mood": last_check.mood.value,
                        "mood_emoji": last_check.mood_emoji,
                        "energy": last_check.energy.value,
                        "energy_bars": last_check.energy_bars,
                        "workload": round(member.workload_percentage, 1),
                        "is_concerning": last_check.is_concerning
                    }
                    
                    # Adiciona burnout risk se disponível
                    if last_check.ai_burnout_risk:
                        member_data["burnout_risk"] = last_check.ai_burnout_risk
                        burnout_risks.append(last_check.ai_burnout_risk)
                        
                        # Alerta se risco alto
                        if last_check.ai_burnout_risk > 70:
                            team_summary["alerts"].append({
                                "severity": "high",
                                "user": member.full_name,
                                "type": "burnout_risk",
                                "message": f"{member.full_name} apresenta alto risco de burnout ({last_check.ai_burnout_risk}%)"
                            })
                    
                    # Alerta se sobrecarregado
                    if member.is_overloaded:
                        team_summary["alerts"].append({
                            "severity": "medium",
                            "user": member.full_name,
                            "type": "overload",
                            "message": f"{member.full_name} está sobrecarregado ({member.workload_percentage:.0f}% de capacidade)"
                        })
                    
                    # Alerta se bem-estar preocupante
                    if last_check.is_concerning:
                        team_summary["alerts"].append({
                            "severity": "medium",
                            "user": member.full_name,
                            "type": "wellbeing",
                            "message": f"{member.full_name} relatou baixo bem-estar"
                        })
                    
                    team_summary["members_analysis"].append(member_data)
            
            # Calcula médias
            if mood_scores:
                team_summary["average_scores"]["mood"] = round(sum(mood_scores) / len(mood_scores), 1)
            if energy_scores:
                team_summary["average_scores"]["energy"] = round(sum(energy_scores) / len(energy_scores), 1)
            if burnout_risks:
                team_summary["average_scores"]["burnout_risk"] = round(sum(burnout_risks) / len(burnout_risks), 1)
            
            # Determina tendência geral
            if mood_scores:
                avg_mood = sum(mood_scores) / len(mood_scores)
                if avg_mood >= 4:
                    team_summary["trend"] = "positive"
                elif avg_mood <= 2:
                    team_summary["trend"] = "concerning"
            
            # Ordena alertas por severidade
            team_summary["alerts"].sort(
                key=lambda a: {"high": 3, "medium": 2, "low": 1}.get(a["severity"], 0),
                reverse=True
            )
            
            return team_summary
            
        except Exception as e:
            logger.error(f"Erro no resumo da equipe: {str(e)}")
            return {"error": str(e)}
    
    
    def detect_burnout_patterns(
        self,
        user_id: int,
        threshold: int = 70
    ) -> Dict[str, Any]:
        """
        Detecta padrões de burnout
        
        Args:
            user_id: ID do usuário
            threshold: Threshold de risco (0-100)
        
        Returns:
            Análise de padrões de burnout
        """
        try:
            # Busca últimos 30 dias
            since_date = datetime.now() - timedelta(days=30)
            checks = self.db.query(WellbeingCheck).filter(
                WellbeingCheck.user_id == user_id,
                WellbeingCheck.created_at >= since_date
            ).order_by(WellbeingCheck.created_at.asc()).all()
            
            if len(checks) < 3:
                return {
                    "has_pattern": False,
                    "message": "Dados insuficientes para análise de padrões"
                }
            
            # Analisa padrões
            patterns = {
                "declining_mood": self._check_declining_trend([self._mood_to_score(c.mood) for c in checks]),
                "declining_energy": self._check_declining_trend([self._energy_to_score(c.energy) for c in checks]),
                "consistent_low_mood": sum(1 for c in checks if self._mood_to_score(c.mood) <= 2) / len(checks) > 0.5,
                "consistent_low_energy": sum(1 for c in checks if self._energy_to_score(c.energy) <= 2) / len(checks) > 0.5
            }
            
            # Calcula score de risco
            risk_score = 0
            if patterns["declining_mood"]: risk_score += 30
            if patterns["declining_energy"]: risk_score += 30
            if patterns["consistent_low_mood"]: risk_score += 20
            if patterns["consistent_low_energy"]: risk_score += 20
            
            has_burnout_pattern = risk_score >= threshold
            
            return {
                "has_pattern": has_burnout_pattern,
                "risk_score": risk_score,
                "patterns": patterns,
                "severity": "high" if risk_score >= 80 else "medium" if risk_score >= 50 else "low",
                "recommendations": self._get_burnout_recommendations(risk_score, patterns)
            }
            
        except Exception as e:
            logger.error(f"Erro na detecção de burnout: {str(e)}")
            return {"error": str(e)}
    
    
    # ============= HELPERS =============
    
    def _calculate_local_metrics(
        self,
        checks: List[WellbeingCheck]
    ) -> Dict[str, Any]:
        """Calcula métricas locais"""
        if not checks:
            return {}
        
        mood_scores = [self._mood_to_score(c.mood) for c in checks]
        energy_scores = [self._energy_to_score(c.energy) for c in checks]
        
        return {
            "average_mood": round(sum(mood_scores) / len(mood_scores), 2),
            "average_energy": round(sum(energy_scores) / len(energy_scores), 2),
            "mood_distribution": dict(Counter([c.mood.value for c in checks])),
            "energy_distribution": dict(Counter([c.energy.value for c in checks])),
            "concerning_checks": sum(1 for c in checks if c.is_concerning),
            "concerning_percentage": round(sum(1 for c in checks if c.is_concerning) / len(checks) * 100, 1)
        }
    
    
    def _prepare_wellbeing_data(self, check: WellbeingCheck) -> Dict[str, Any]:
        """Prepara dados de bem-estar para IA"""
        return {
            "date": check.created_at.strftime("%Y-%m-%d"),
            "mood": check.mood.value,
            "energy": check.energy.value,
            "notes": check.notes or ""
        }
    
    
    def _prepare_task_data(self, task: Task) -> Dict[str, Any]:
        """Prepara dados de tarefa para IA"""
        return {
            "title": task.title,
            "status": task.status.value,
            "priority": task.priority.value,
            "estimated_hours": task.estimated_hours or 0,
            "actual_hours": task.actual_hours or 0,
            "is_overdue": task.is_overdue
        }
    
    
    def _mood_to_score(self, mood: MoodLevel) -> int:
        """Converte mood para score numérico"""
        scores = {
            MoodLevel.VERY_BAD: 1,
            MoodLevel.BAD: 2,
            MoodLevel.NEUTRAL: 3,
            MoodLevel.GOOD: 4,
            MoodLevel.VERY_GOOD: 5
        }
        return scores.get(mood, 3)
    
    
    def _energy_to_score(self, energy: EnergyLevel) -> int:
        """Converte energy para score numérico"""
        scores = {
            EnergyLevel.EXHAUSTED: 1,
            EnergyLevel.LOW: 2,
            EnergyLevel.MEDIUM: 3,
            EnergyLevel.HIGH: 4,
            EnergyLevel.VERY_HIGH: 5
        }
        return scores.get(energy, 3)
    
    
    def _check_declining_trend(self, scores: List[int]) -> bool:
        """Verifica se há tendência de declínio"""
        if len(scores) < 3:
            return False
        
        # Compara últimos 3 com primeiros 3
        recent = scores[-3:]
        older = scores[:3]
        
        avg_recent = sum(recent) / len(recent)
        avg_older = sum(older) / len(older)
        
        return avg_recent < avg_older - 0.5
    
    
    def _get_burnout_recommendations(
        self,
        risk_score: int,
        patterns: Dict[str, bool]
    ) -> List[str]:
        """Gera recomendações baseadas no risco"""
        recommendations = []
        
        if risk_score >= 70:
            recommendations.append("Atenção urgente necessária - considere conversa individual")
            recommendations.append("Sugira redução de carga ou redistribuição de tarefas")
            recommendations.append("Considere encaminhamento para suporte profissional")
        
        if patterns.get("declining_mood"):
            recommendations.append("Humor em declínio - ofereça suporte emocional")
        
        if patterns.get("declining_energy"):
            recommendations.append("Energia em queda - verifique possível sobrecarga")
        
        if patterns.get("consistent_low_energy"):
            recommendations.append("Baixa energia consistente - sugira pausas e descanso")
        
        if not recommendations:
            recommendations.append("Continue monitorando regularmente")
        
        return recommendations
