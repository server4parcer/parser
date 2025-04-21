"""
API Authentication - Модуль аутентификации для API парсера YCLIENTS.

Модуль предоставляет функции для проверки API-ключа.
"""
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from config.settings import API_KEY


logger = logging.getLogger(__name__)

# Заголовок API-ключа
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: str = Depends(api_key_header)):
    """
    Проверка API-ключа.
    
    Args:
        api_key: API-ключ из заголовка запроса
        
    Returns:
        str: Валидный API-ключ
        
    Raises:
        HTTPException: Если API-ключ отсутствует или недействителен
    """
    if not api_key:
        logger.warning("API-ключ отсутствует в запросе")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API-ключ не предоставлен",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key != API_KEY:
        logger.warning(f"Недействительный API-ключ: {api_key}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недействительный API-ключ",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key
