from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Engine do SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obter sessão do banco de dados
    
    Yields:
        Session: Sessão do SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Inicializa o banco de dados
    Cria todas as tabelas se não existirem
    """
    try:
        from app.models import user, task, skill, wellbeing
        
        logger.info("Criando tabelas do banco de dados...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas criadas com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {str(e)}")
        raise


def create_initial_data(db: Session) -> None:
    """
    Cria dados iniciais no banco
    
    Args:
        db: Sessão do banco de dados
    """
    try:
        from app.models.user import User, UserRole
        from app.models.skill import Skill
        from passlib.context import CryptContext
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Verifica se já existem dados
        existing_users = db.query(User).count()
        if existing_users > 0:
            logger.info("Banco já possui dados. Pulando criação inicial.")
            return
        
        logger.info("Criando dados iniciais...")
        
        # Cria usuário admin
        admin = User(
            email="admin@ideiatech.com",
            username="admin",
            full_name="Administrador",
            hashed_password=pwd_context.hash("Admin@123"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            department="TI",
            position="Administrador do Sistema"
        )
        db.add(admin)
        
        # Cria gestor de exemplo
        manager = User(
            email="gestor@ideiatech.com",
            username="gestor",
            full_name="João Silva",
            hashed_password=pwd_context.hash("Gestor@123"),
            role=UserRole.GESTOR,
            is_active=True,
            is_verified=True,
            department="Tecnologia",
            position="Gerente de Projetos"
        )
        db.add(manager)
        
        db.commit()
        db.refresh(manager)
        
        # Cria colaboradores de exemplo
        colaboradores = [
            {
                "email": "maria@ideiatech.com",
                "username": "maria.santos",
                "full_name": "Maria Santos",
                "position": "Desenvolvedora Full Stack"
            },
            {
                "email": "pedro@ideiatech.com",
                "username": "pedro.oliveira",
                "full_name": "Pedro Oliveira",
                "position": "Analista de Dados"
            },
            {
                "email": "ana@ideiatech.com",
                "username": "ana.costa",
                "full_name": "Ana Costa",
                "position": "Designer UX/UI"
            }
        ]
        
        for colab_data in colaboradores:
            colab = User(
                email=colab_data["email"],
                username=colab_data["username"],
                full_name=colab_data["full_name"],
                hashed_password=pwd_context.hash("Colaborador@123"),
                role=UserRole.COLABORADOR,
                is_active=True,
                is_verified=True,
                department="Tecnologia",
                position=colab_data["position"],
                manager_id=manager.id
            )
            db.add(colab)
        
        # Cria skills de exemplo
        skills_data = [
            {"name": "Python", "category": "Linguagens", "description": "Linguagem de programação"},
            {"name": "JavaScript", "category": "Linguagens", "description": "Linguagem de programação web"},
            {"name": "React", "category": "Frameworks", "description": "Framework frontend"},
            {"name": "React Native", "category": "Frameworks", "description": "Framework mobile"},
            {"name": "Node.js", "category": "Frameworks", "description": "Runtime JavaScript"},
            {"name": "SQL", "category": "Banco de Dados", "description": "Linguagem de consulta"},
            {"name": "Git", "category": "Ferramentas", "description": "Controle de versão"},
            {"name": "Docker", "category": "Ferramentas", "description": "Containerização"},
            {"name": "AWS", "category": "Cloud", "description": "Amazon Web Services"},
            {"name": "Figma", "category": "Design", "description": "Ferramenta de design"},
            {"name": "Comunicação", "category": "Soft Skills", "description": "Habilidade de comunicação"},
            {"name": "Trabalho em Equipe", "category": "Soft Skills", "description": "Colaboração"},
        ]
        
        for skill_data in skills_data:
            skill = Skill(**skill_data)
            db.add(skill)
        
        db.commit()
        logger.info("Dados iniciais criados com sucesso!")
        logger.info("Credenciais de acesso:")
        logger.info("  Admin: admin / Admin@123")
        logger.info("  Gestor: gestor / Gestor@123")
        logger.info("  Colaborador: maria.santos / Colaborador@123")
        
    except Exception as e:
        logger.error(f"Erro ao criar dados iniciais: {str(e)}")
        db.rollback()
        raise
