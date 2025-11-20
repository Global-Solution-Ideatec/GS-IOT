"""
Google Gemini AI Service - IdeiaTech
Serviço principal de integração com Gemini API
"""
import google.generativeai as genai
from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Serviço de integração com Google Gemini AI"""
    
    def __init__(self):
        """Inicializa o serviço Gemini"""
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini AI inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar Gemini: {str(e)}")
            raise
    
    
    def generate_task_recommendation(
        self,
        task: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        team_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Gera recomendação inteligente de quem deve receber a tarefa
        
        Args:
            task: Dicionário com dados da tarefa
            candidates: Lista de colaboradores candidatos
            team_context: Contexto adicional da equipe
        
        Returns:
            Dicionário com recomendação e justificativa
        """
        try:
            prompt = self._build_task_recommendation_prompt(task, candidates, team_context)
            
            logger.info(f"Gerando recomendação para tarefa: {task.get('title', 'N/A')}")
            
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            logger.info(f"Recomendação gerada com sucesso")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao gerar recomendação: {str(e)}")
            return self._fallback_recommendation(candidates)
    
    
    def analyze_wellbeing_trend(
        self,
        user_name: str,
        wellbeing_history: List[Dict[str, Any]],
        recent_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analisa tendências de bem-estar do colaborador
        
        Args:
            user_name: Nome do colaborador
            wellbeing_history: Histórico de check-ins
            recent_tasks: Tarefas recentes
        
        Returns:
            Análise com insights e recomendações
        """
        try:
            prompt = self._build_wellbeing_analysis_prompt(
                user_name, wellbeing_history, recent_tasks
            )
            
            logger.info(f"Analisando bem-estar de: {user_name}")
            
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            logger.info("Análise de bem-estar concluída")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na análise de bem-estar: {str(e)}")
            return self._fallback_wellbeing_analysis()
    
    
    def generate_skill_development_plan(
        self,
        user_profile: Dict[str, Any],
        current_skills: List[Dict[str, Any]],
        target_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gera plano de desenvolvimento de habilidades
        
        Args:
            user_profile: Perfil do colaborador
            current_skills: Habilidades atuais
            target_role: Cargo alvo (opcional)
        
        Returns:
            Plano de desenvolvimento personalizado
        """
        try:
            prompt = self._build_skill_development_prompt(
                user_profile, current_skills, target_role
            )
            
            logger.info(f"Gerando plano de desenvolvimento para: {user_profile.get('name', 'N/A')}")
            
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            logger.info("Plano de desenvolvimento gerado")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao gerar plano: {str(e)}")
            return self._fallback_development_plan()
    
    
    def generate_team_insights(
        self,
        team_data: Dict[str, Any],
        time_period: str = "week"
    ) -> Dict[str, Any]:
        """
        Gera insights sobre a equipe para o gestor
        
        Args:
            team_data: Dados da equipe
            time_period: Período de análise
        
        Returns:
            Insights e recomendações gerenciais
        """
        try:
            prompt = self._build_team_insights_prompt(team_data, time_period)
            
            logger.info("Gerando insights da equipe")
            
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            logger.info("Insights da equipe gerados")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao gerar insights: {str(e)}")
            return self._fallback_team_insights()
    
    
    # ============= PROMPT BUILDERS =============
    
    def _build_task_recommendation_prompt(
        self,
        task: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        team_context: Optional[Dict[str, Any]]
    ) -> str:
        """Constrói prompt para recomendação de tarefa"""
        
        candidates_info = "\n".join([
            f"- {c['name']}: "
            f"Skills: {', '.join(c.get('skills', []))}, "
            f"Carga atual: {c.get('workload', 0)}%, "
            f"Energia: {c.get('energy', 'medium')}, "
            f"Humor: {c.get('mood', 'neutral')}"
            for c in candidates
        ])
        
        context_info = ""
        if team_context:
            context_info = f"\n\nContexto da equipe:\n{json.dumps(team_context, indent=2, ensure_ascii=False)}"
        
        prompt = f"""
Você é o SmartLeader AI, um sistema inteligente de distribuição de tarefas da IdeiaTech.

# TAREFA A SER ATRIBUÍDA
Título: {task.get('title', 'N/A')}
Descrição: {task.get('description', 'N/A')}
Prioridade: {task.get('priority', 'medium')}
Horas estimadas: {task.get('estimated_hours', 'N/A')}
Skills necessárias: {', '.join(task.get('required_skills', []))}
Prazo: {task.get('due_date', 'N/A')}

# COLABORADORES CANDIDATOS
{candidates_info}
{context_info}

# SUA MISSÃO
Analise os dados e recomende qual colaborador é mais adequado para esta tarefa, considerando:
1. Match de habilidades (skills)
2. Carga de trabalho atual (evite sobrecarga)
3. Bem-estar (energia e humor)
4. Equilíbrio e justiça na distribuição

# RESPOSTA ESPERADA (JSON)
Retorne APENAS um JSON válido no seguinte formato:
{{
    "recommended_user_id": <id_do_colaborador>,
    "recommended_user_name": "<nome>",
    "match_score": <0-100>,
    "reasoning": "<explicação clara e concisa em português>",
    "pros": ["<vantagem 1>", "<vantagem 2>"],
    "cons": ["<desvantagem 1>", "<desvantagem 2>"],
    "alternative_user_id": <id_alternativo>,
    "alternative_user_name": "<nome_alternativo>",
    "warnings": ["<aviso se houver sobrecarga ou risco>"]
}}

Seja objetivo, humanizado e focado no bem-estar da equipe.
"""
        return prompt
    
    
    def _build_wellbeing_analysis_prompt(
        self,
        user_name: str,
        wellbeing_history: List[Dict[str, Any]],
        recent_tasks: List[Dict[str, Any]]
    ) -> str:
        """Constrói prompt para análise de bem-estar"""
        
        history_summary = "\n".join([
            f"- {w.get('date', 'N/A')}: Humor={w.get('mood', 'N/A')}, "
            f"Energia={w.get('energy', 'N/A')}, Nota={w.get('notes', 'Sem nota')}"
            for w in wellbeing_history[-10:]  # Últimos 10
        ])
        
        tasks_summary = "\n".join([
            f"- {t.get('title', 'N/A')} (Status: {t.get('status', 'N/A')}, "
            f"Horas: {t.get('actual_hours', 0)}/{t.get('estimated_hours', 0)})"
            for t in recent_tasks[-5:]  # Últimas 5
        ])
        
        prompt = f"""
Você é o SmartLeader AI, especialista em análise de bem-estar e saúde mental no trabalho.

# COLABORADOR
Nome: {user_name}

# HISTÓRICO DE BEM-ESTAR (últimos check-ins)
{history_summary}

# TAREFAS RECENTES
{tasks_summary}

# SUA MISSÃO
Analise o histórico e identifique:
1. Tendências de humor e energia
2. Padrões preocupantes
3. Sinais de burnout ou sobrecarga
4. Recomendações personalizadas

# RESPOSTA ESPERADA (JSON)
Retorne APENAS um JSON válido no seguinte formato:
{{
    "sentiment_score": <-100 a +100>,
    "burnout_risk": <0-100>,
    "trend": "<improving|stable|declining>",
    "main_concerns": ["<preocupação 1>", "<preocupação 2>"],
    "positive_aspects": ["<aspecto positivo 1>", "<aspecto positivo 2>"],
    "recommendations": [
        {{
            "type": "<break|task_reduction|support|recognition>",
            "description": "<recomendação específica>",
            "priority": "<low|medium|high>"
        }}
    ],
    "manager_alert": "<mensagem para o gestor se houver risco>",
    "motivational_message": "<mensagem motivacional personalizada para o colaborador>"
}}

Seja empático, construtivo e focado no bem-estar.
"""
        return prompt
    
    
    def _build_skill_development_prompt(
        self,
        user_profile: Dict[str, Any],
        current_skills: List[Dict[str, Any]],
        target_role: Optional[str]
    ) -> str:
        """Constrói prompt para plano de desenvolvimento"""
        
        skills_info = "\n".join([
            f"- {s.get('name', 'N/A')}: Nível {s.get('level', 'N/A')} "
            f"({s.get('proficiency_score', 0)}%)"
            for s in current_skills
        ])
        
        target_info = f"\nCargo alvo: {target_role}" if target_role else ""
        
        prompt = f"""
Você é o SmartLeader AI, especialista em desenvolvimento profissional.

# COLABORADOR
Nome: {user_profile.get('name', 'N/A')}
Cargo atual: {user_profile.get('position', 'N/A')}
Departamento: {user_profile.get('department', 'N/A')}
{target_info}

# HABILIDADES ATUAIS
{skills_info}

# SUA MISSÃO
Crie um plano de desenvolvimento personalizado:
1. Identifique gaps de habilidades
2. Sugira áreas de melhoria
3. Recomende ações concretas
4. Priorize baseado no perfil atual

# RESPOSTA ESPERADA (JSON)
Retorne APENAS um JSON válido no seguinte formato:
{{
    "skill_gaps": [
        {{
            "skill_name": "<habilidade faltante>",
            "importance": "<low|medium|high>",
            "reason": "<por que é importante>"
        }}
    ],
    "improvement_areas": [
        {{
            "current_skill": "<habilidade existente>",
            "current_level": "<nível atual>",
            "target_level": "<nível alvo>",
            "action_plan": "<como melhorar>"
        }}
    ],
    "learning_recommendations": [
        {{
            "type": "<course|project|mentoring|practice>",
            "title": "<título da recomendação>",
            "description": "<descrição detalhada>",
            "estimated_duration": "<tempo estimado>",
            "priority": "<low|medium|high>"
        }}
    ],
    "strengths": ["<força 1>", "<força 2>"],
    "next_steps": ["<próximo passo 1>", "<próximo passo 2>"],
    "timeline": "<sugestão de cronograma>"
}}

Seja motivador, realista e focado em crescimento sustentável.
"""
        return prompt
    
    
    def _build_team_insights_prompt(
        self,
        team_data: Dict[str, Any],
        time_period: str
    ) -> str:
        """Constrói prompt para insights da equipe"""
        
        prompt = f"""
Você é o SmartLeader AI, assistente executivo para gestão de equipes.

# DADOS DA EQUIPE ({time_period})
{json.dumps(team_data, indent=2, ensure_ascii=False)}

# SUA MISSÃO
Analise os dados e forneça insights acionáveis para o gestor:
1. Panorama geral da equipe
2. Alertas e riscos
3. Oportunidades de melhoria
4. Recomendações estratégicas

# RESPOSTA ESPERADA (JSON)
Retorne APENAS um JSON válido no seguinte formato:
{{
    "summary": "<resumo executivo em 2-3 linhas>",
    "team_health_score": <0-100>,
    "productivity_score": <0-100>,
    "wellbeing_score": <0-100>,
    "key_insights": [
        {{
            "category": "<productivity|wellbeing|skills|distribution>",
            "insight": "<insight específico>",
            "impact": "<low|medium|high>"
        }}
    ],
    "alerts": [
        {{
            "type": "<overload|burnout|skill_gap|inequality>",
            "severity": "<low|medium|high|critical>",
            "affected_users": ["<nome1>", "<nome2>"],
            "description": "<descrição do alerta>",
            "suggested_action": "<ação recomendada>"
        }}
    ],
    "opportunities": [
        {{
            "area": "<área de oportunidade>",
            "description": "<descrição>",
            "potential_impact": "<impacto esperado>"
        }}
    ],
    "recommendations": [
        {{
            "priority": "<low|medium|high>",
            "action": "<ação recomendada>",
            "expected_outcome": "<resultado esperado>",
            "estimated_effort": "<esforço estimado>"
        }}
    ],
    "top_performers": ["<nome1>", "<nome2>"],
    "needs_attention": ["<nome1>", "<nome2>"]
}}

Seja estratégico, objetivo e focado em ações concretas.
"""
        return prompt
    
    
    # ============= HELPERS =============
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON da resposta do Gemini"""
        try:
            # Remove possíveis markdown code blocks
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()
            
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao fazer parse do JSON: {str(e)}")
            logger.error(f"Resposta original: {response_text}")
            return {"error": "Erro ao processar resposta da IA", "raw_response": response_text}
    
    
    def _fallback_recommendation(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Recomendação fallback se a IA falhar"""
        if not candidates:
            return {"error": "Nenhum candidato disponível"}
        
        # Escolhe o candidato com menor carga
        best_candidate = min(candidates, key=lambda c: c.get('workload', 100))
        
        return {
            "recommended_user_id": best_candidate.get('id'),
            "recommended_user_name": best_candidate.get('name'),
            "match_score": 50,
            "reasoning": "Seleção automática baseada em menor carga de trabalho (IA indisponível)",
            "pros": ["Menor carga atual"],
            "cons": ["Recomendação sem análise completa de IA"],
            "warnings": ["Sistema de IA temporariamente indisponível"]
        }
    
    
    def _fallback_wellbeing_analysis(self) -> Dict[str, Any]:
        """Análise fallback se a IA falhar"""
        return {
            "sentiment_score": 0,
            "burnout_risk": 0,
            "trend": "stable",
            "main_concerns": ["Análise de IA indisponível"],
            "positive_aspects": [],
            "recommendations": [],
            "manager_alert": None,
            "motivational_message": "Continue se cuidando! Sua saúde é importante."
        }
    
    
    def _fallback_development_plan(self) -> Dict[str, Any]:
        """Plano fallback se a IA falhar"""
        return {
            "skill_gaps": [],
            "improvement_areas": [],
            "learning_recommendations": [],
            "strengths": ["A análise detalhada está temporariamente indisponível"],
            "next_steps": ["Tente novamente mais tarde"],
            "timeline": "N/A"
        }
    
    
    def _fallback_team_insights(self) -> Dict[str, Any]:
        """Insights fallback se a IA falhar"""
        return {
            "summary": "Análise de equipe temporariamente indisponível",
            "team_health_score": 0,
            "productivity_score": 0,
            "wellbeing_score": 0,
            "key_insights": [],
            "alerts": [],
            "opportunities": [],
            "recommendations": [],
            "top_performers": [],
            "needs_attention": []
        }


# Instância global do serviço
gemini_service = GeminiService()
