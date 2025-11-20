"""
Model de Bem-estar - IdeiaTech
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.user import Base


class MoodLevel(str, enum.Enum):
    """Nível de humor"""
    VERY_BAD = "very_bad"      
    BAD = "bad"                
    NEUTRAL = "neutral"       
    GOOD = "good"             
    VERY_GOOD = "very_good"    


class EnergyLevel(str, enum.Enum):
    """Nível de energia"""
    EXHAUSTED = "exhausted"    # 🔋 (vazio)
    LOW = "low"                # 🔋🔋
    MEDIUM = "medium"          # 🔋🔋🔋
    HIGH = "high"              # 🔋🔋🔋🔋
    VERY_HIGH = "very_high"    # 🔋🔋🔋🔋🔋


class WellbeingCheck(Base):
    """Model de Check-in de Bem-estar"""
    __tablename__ = "wellbeing_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Níveis reportados
    mood = Column(SQLEnum(MoodLevel), nullable=False)
    energy = Column(SQLEnum(EnergyLevel), nullable=False)
    
    # Nota opcional do usuário
    notes = Column(Text, nullable=True)
    
    # Análise da IA
    ai_sentiment_score = Column(Integer, nullable=True)  # -100 (negativo) a +100 (positivo)
    ai_burnout_risk = Column(Integer, nullable=True)  # 0-100 (risco de burnout)
    ai_recommendations = Column(Text, nullable=True)  # Recomendações da IA em JSON
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relacionamentos
    user = relationship("User", back_populates="wellbeing_checks")
    
    def __repr__(self):
        return f"<WellbeingCheck(user_id={self.user_id}, mood='{self.mood}', energy='{self.energy}')>"
    
    @property
    def mood_emoji(self) -> str:
        """Retorna emoji correspondente ao humor"""
        emojis = {
            MoodLevel.VERY_BAD: "😞",
            MoodLevel.BAD: "😟",
            MoodLevel.NEUTRAL: "😐",
            MoodLevel.GOOD: "🙂",
            MoodLevel.VERY_GOOD: "😄"
        }
        return emojis.get(self.mood, "😐")
    
    @property
    def energy_bars(self) -> str:
        """Retorna barras de energia visuais"""
        bars = {
            EnergyLevel.EXHAUSTED: "🔋",
            EnergyLevel.LOW: "🔋🔋",
            EnergyLevel.MEDIUM: "🔋🔋🔋",
            EnergyLevel.HIGH: "🔋🔋🔋🔋",
            EnergyLevel.VERY_HIGH: "🔋🔋🔋🔋🔋"
        }
        return bars.get(self.energy, "🔋")
    
    @property
    def is_concerning(self) -> bool:
        """Verifica se o check-in é preocupante"""
        concerning_moods = [MoodLevel.VERY_BAD, MoodLevel.BAD]
        low_energy = [EnergyLevel.EXHAUSTED, EnergyLevel.LOW]
        return self.mood in concerning_moods or self.energy in low_energy
