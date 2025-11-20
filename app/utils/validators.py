"""
Validadores - IdeiaTech
"""
import re
from typing import Optional


def validate_email(email: str) -> bool:
    """
    Valida formato de email
    
    Args:
        email: Email a ser validado
    
    Returns:
        True se válido, False caso contrário
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Valida força de senha
    
    Requisitos:
    - Mínimo 8 caracteres
    - Pelo menos uma letra maiúscula
    - Pelo menos uma letra minúscula
    - Pelo menos um número
    - Pelo menos um caractere especial
    
    Args:
        password: Senha a ser validada
    
    Returns:
        Tupla (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Senha deve ter no mínimo 8 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    if not re.search(r'\d', password):
        return False, "Senha deve conter pelo menos um número"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Senha deve conter pelo menos um caractere especial"
    
    return True, None


def validate_workload_hours(hours: int, capacity: int) -> tuple[bool, Optional[str]]:
    """
    Valida carga de trabalho
    
    Args:
        hours: Horas a serem adicionadas
        capacity: Capacidade total do usuário
    
    Returns:
        Tupla (is_valid, error_message)
    """
    if hours < 0:
        return False, "Horas não podem ser negativas"
    
    if hours > capacity:
        return False, f"Carga excede capacidade máxima de {capacity} horas"
    
    return True, None


def sanitize_string(text: str, max_length: int = 255) -> str:
    """
    Limpa e sanitiza strings
    
    Args:
        text: Texto a ser sanitizado
        max_length: Comprimento máximo
    
    Returns:
        Texto sanitizado
    """
    if not text:
        return ""
    
    # Remove espaços extras
    text = " ".join(text.split())
    
    # Trunca se necessário
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()
