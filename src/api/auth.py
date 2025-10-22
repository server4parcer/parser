"""
API Authentication - Модуль аутентификации для API парсера YCLIENTS.

Модуль предоставляет функции для проверки API-ключа.
"""
import logging
from fastapi import Depends, HTTPException, status, Query
from fastapi.security.api_key import APIKeyHeader

from config.settings import API_KEY


logger = logging.getLogger(__name__)

# Заголовок API-ключа
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key_header: str = Depends(api_key_header), api_key: str = Query(None, alias="api_key")):
    """
    Проверка API-ключа.

    Args:
        api_key_header: API-ключ из заголовка запроса
        api_key: API-ключ из параметра запроса (используем alias 'api_key')

    Returns:
        str: Валидный API-ключ

    Raises:
        HTTPException: Если API-ключ отсутствует или недействителен
    """
    # Ищем API ключ в заголовке или параметрах запроса
    key_to_check = api_key_header or api_key

    if not key_to_check:
        logger.warning("API-ключ отсутствует в запросе")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API-ключ не предоставлен",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if key_to_check != API_KEY:
        logger.warning(f"Недействительный API-ключ: {key_to_check}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недействительный API-ключ",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return key_to_check
