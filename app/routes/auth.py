"""
Rotas de Autenticação - IdeiaTech
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import timedelta
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import logging

from app.config import settings
from app.models.user import User, UserRole
from app.utils.jwt_handler import create_access_token, get_current_user
from app.utils.validators import validate_email, validate_password

logger = logging.getLogger(__name__)
router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============= SCHEMAS =============

class UserRegister(BaseModel):
    """Schema para registro de usuário"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8)
    department: Optional[str] = None
    position: Optional[str] = None


class Token(BaseModel):
    """Schema para token JWT"""
    access_token: str
    token_type: str
    user: dict


class UserResponse(BaseModel):
    """Schema para resposta de usuário"""
    id: int
    email: str
    username: str
    full_name: str
    role: str
    department: Optional[str]
    position: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True


# ============= DEPENDENCY =============

def get_db():
    """Dependency de banco de dados (placeholder)"""
    # TODO: Implementar depois com database.py
    pass


# ============= ENDPOINTS =============

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Registra um novo colaborador
    
    - **email**: Email válido (único)
    - **username**: Nome de usuário (único)
    - **full_name**: Nome completo
    - **password**: Senha forte (mín. 8 caracteres)
    - **department**: Departamento (opcional)
    - **position**: Cargo (opcional)
    """
    try:
        # Valida email
        if not validate_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email inválido"
            )
        
        # Valida senha
        is_valid_pwd, error_msg = validate_password(user_data.password)
        if not is_valid_pwd:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Verifica duplicatas
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email ou username já cadastrado"
            )
        
        # Cria usuário
        hashed_password = pwd_context.hash(user_data.password)
        
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            department=user_data.department,
            position=user_data.position,
            role=UserRole.COLABORADOR,  # Sempre colaborador no registro
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"Novo usuário registrado: {new_user.username}")
        
        # Cria token
        access_token = create_access_token(
            data={"sub": str(new_user.id), "role": new_user.role.value}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "username": new_user.username,
                "full_name": new_user.full_name,
                "role": new_user.role.value
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no registro: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao registrar usuário"
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login com username e password
    
    Retorna token JWT para autenticação
    """
    try:
        # Busca usuário (username ou email)
        user = db.query(User).filter(
            (User.username == form_data.username) | (User.email == form_data.username)
        ).first()
        
        # Verifica credenciais
        if not user or not pwd_context.verify(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verifica se está ativo
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo"
            )
        
        # Atualiza último login
        from datetime import datetime
        user.last_login = datetime.now()
        db.commit()
        
        logger.info(f"Login bem-sucedido: {user.username}")
        
        # Cria token
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value,
                "department": user.department,
                "position": user.position
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao fazer login"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Retorna informações do usuário autenticado
    
    Requer autenticação (Bearer token)
    """
    return current_user


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout (token deve ser invalidado no cliente)
    """
    logger.info(f"Logout: {current_user.username}")
    return {"message": "Logout realizado com sucesso"}
