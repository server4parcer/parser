"""
Main - Главный скрипт для запуска парсера YCLIENTS.

Этот скрипт является точкой входа в приложение.
"""
import asyncio
import logging
import sys
import argparse
import uvicorn
from typing import List, Optional

from config.logging_config import setup_logging
from config.settings import (
    API_HOST, API_PORT, API_DEBUG, 
    DEFAULT_URLS, PARSE_INTERVAL
)
from src.database.db_manager import DatabaseManager
from src.parser.yclients_parser import YClientsParser
from src.api.routes import app


# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)


async def run_api_server() -> None:
    """Запуск API-сервера."""
    logger.info("Запуск API-сервера")
    
    # API-сервер запускается в отдельном процессе с помощью uvicorn
    uvicorn.run(
        "src.api.routes:app",
        host=API_HOST,
        port=API_PORT,
        log_level="info" if API_DEBUG else "warning",
        reload=API_DEBUG
    )


async def run_parser(urls: List[str], continuous: bool = True) -> None:
    """
    Запуск парсера YCLIENTS.
    
    Args:
        urls: Список URL для парсинга
        continuous: Флаг непрерывного парсинга
    """
    logger.info(f"Запуск парсера для {len(urls)} URL")
    
    # Инициализация менеджера базы данных
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    try:
        # Инициализация парсера
        parser = YClientsParser(urls, db_manager)
        
        if continuous:
            # Запуск непрерывного парсинга
            await parser.run_continuous()
        else:
            # Запуск одной итерации парсинга
            await parser.run_single_iteration()
        
    except KeyboardInterrupt:
        logger.info("Парсер остановлен пользователем")
    
    except Exception as e:
        logger.error(f"Ошибка при выполнении парсинга: {str(e)}")
    
    finally:
        # Закрытие соединения с базой данных
        await db_manager.close()


async def run_all(urls: List[str]) -> None:
    """
    Запуск всех компонентов приложения: парсера и API-сервера.
    
    Args:
        urls: Список URL для парсинга
    """
    logger.info("Запуск всех компонентов приложения")
    
    # Создаем задачи для запуска парсера и API-сервера
    api_task = asyncio.create_task(run_api_server())
    parser_task = asyncio.create_task(run_parser(urls))
    
    # Ожидаем завершения задач
    await asyncio.gather(api_task, parser_task)


def parse_arguments():
    """
    Парсинг аргументов командной строки.
    
    Returns:
        argparse.Namespace: Аргументы командной строки
    """
    parser = argparse.ArgumentParser(description="YCLIENTS Parser")
    
    # Режим работы
    parser.add_argument(
        "--mode",
        choices=["parser", "api", "all"],
        default="all",
        help="Режим работы: parser (только парсер), api (только API-сервер), all (парсер и API-сервер)"
    )
    
    # URL для парсинга
    parser.add_argument(
        "--urls",
        nargs="+",
        help="URL для парсинга (разделенные пробелами)"
    )
    
    # Флаг одноразового запуска
    parser.add_argument(
        "--once",
        action="store_true",
        help="Запустить парсер только один раз (без непрерывного режима)"
    )
    
    # Интервал обновления
    parser.add_argument(
        "--interval",
        type=int,
        default=PARSE_INTERVAL,
        help=f"Интервал обновления данных в секундах (по умолчанию {PARSE_INTERVAL})"
    )
    
    return parser.parse_args()


async def main():
    """Основная функция приложения."""
    # Парсинг аргументов командной строки
    args = parse_arguments()
    
    # Определение списка URL для парсинга
    urls = args.urls if args.urls else DEFAULT_URLS
    
    if not urls and args.mode in ["parser", "all"]:
        logger.error("Не указаны URL для парсинга")
        print("Ошибка: не указаны URL для парсинга")
        print("Используйте --urls для указания URL или добавьте URL в настройки")
        sys.exit(1)
    
    # Устанавливаем интервал обновления
    global PARSE_INTERVAL
    PARSE_INTERVAL = args.interval
    
    # Запуск в выбранном режиме
    if args.mode == "parser":
        await run_parser(urls, not args.once)
    elif args.mode == "api":
        await run_api_server()
    else:  # all
        await run_all(urls)


if __name__ == "__main__":
    # Запуск основной функции
    asyncio.run(main())
