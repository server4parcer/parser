"""
Main - Главный скрипт для запуска парсера YCLIENTS.
Исправленная версия для работы в Docker окружении Timeweb.
"""
import asyncio
import logging
import sys
import os
import argparse
import uvicorn
from typing import List, Optional

# Исправляем пути для работы в Docker
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Безопасные импорты с fallback
try:
    from config.logging_config import setup_logging
except ImportError:
    # Fallback настройка логирования
    def setup_logging():
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

try:
    from config.settings import (
        API_HOST, API_PORT, API_DEBUG, 
        DEFAULT_URLS, PARSE_INTERVAL
    )
except ImportError:
    # Fallback настройки
    API_HOST = os.environ.get("API_HOST", "0.0.0.0")
    API_PORT = int(os.environ.get("API_PORT", "8000"))
    API_DEBUG = os.environ.get("API_DEBUG", "false").lower() == "true"
    PARSE_INTERVAL = int(os.environ.get("PARSE_INTERVAL", "600"))
    
    # Получаем URL из переменных окружения
    url_env = os.environ.get("PARSE_URLS", "")
    DEFAULT_URLS = [url.strip() for url in url_env.split(",") if url.strip()] if url_env else []

try:
    from src.database.db_manager import DatabaseManager
    from src.parser.yclients_parser import YClientsParser
    from src.api.routes import app
except ImportError:
    # Пробуем импорт без src prefix
    from database.db_manager import DatabaseManager
    from parser.yclients_parser import YClientsParser
    from api.routes import app

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

async def run_api_server() -> None:
    """Запуск API-сервера."""
    logger.info("🚀 Запуск API-сервера")
    
    try:
        # API-сервер запускается в отдельном процессе
        config = uvicorn.Config(
            "src.api.routes:app" if "src" in sys.modules else "api.routes:app",
            host=API_HOST,
            port=API_PORT,
            log_level="info" if API_DEBUG else "warning",
            reload=False  # Отключаем reload в продакшене
        )
        server = uvicorn.Server(config)
        await server.serve()
    except Exception as e:
        logger.error(f"❌ Ошибка запуска API сервера: {e}")

async def run_parser(urls: List[str], continuous: bool = True) -> None:
    """
    Запуск парсера YCLIENTS.
    """
    logger.info(f"🎯 Запуск парсера для {len(urls)} URL")
    
    # Инициализация менеджера базы данных
    db_manager = DatabaseManager()
    
    try:
        await db_manager.initialize()
        logger.info("✅ База данных инициализирована")
        
        # Инициализация парсера
        parser = YClientsParser(urls, db_manager)
        
        if continuous:
            logger.info(f"🔄 Запуск непрерывного парсинга (интервал: {PARSE_INTERVAL}с)")
            await parser.run_continuous()
        else:
            logger.info("⚡ Запуск одноразового парсинга")
            await parser.run_single_iteration()
        
    except KeyboardInterrupt:
        logger.info("⛔ Парсер остановлен пользователем")
    
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении парсинга: {str(e)}")
        raise
    
    finally:
        try:
            await db_manager.close()
            logger.info("✅ Соединение с базой данных закрыто")
        except Exception as e:
            logger.error(f"⚠️ Ошибка при закрытии БД: {e}")

async def run_all(urls: List[str]) -> None:
    """
    Запуск всех компонентов приложения.
    """
    logger.info("🚀 Запуск всех компонентов приложения")
    
    # Создаем задачи для запуска парсера и API-сервера
    tasks = []
    
    # API задача
    api_task = asyncio.create_task(run_api_server())
    tasks.append(api_task)
    logger.info("📡 API задача создана")
    
    # Парсер задача (если есть URL)
    if urls:
        parser_task = asyncio.create_task(run_parser(urls))
        tasks.append(parser_task)
        logger.info("🎯 Парсер задача создана")
    else:
        logger.warning("⚠️ URL для парсинга не указаны, запускается только API")
    
    # Ожидаем завершения задач
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"❌ Ошибка в задачах: {e}")

def parse_arguments():
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(description="YClients Parser для Timeweb")
    
    parser.add_argument(
        "--mode",
        choices=["parser", "api", "all"],
        default="all",
        help="Режим работы"
    )
    
    parser.add_argument(
        "--urls",
        nargs="+",
        help="URL для парсинга"
    )
    
    parser.add_argument(
        "--once",
        action="store_true",
        help="Запуск парсера один раз"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=PARSE_INTERVAL,
        help=f"Интервал обновления (по умолчанию {PARSE_INTERVAL}с)"
    )
    
    return parser.parse_args()

async def main():
    """Основная функция приложения."""
    logger.info("🎉 YClients Parser запускается")
    logger.info(f"🐳 Режим: Docker/Timeweb")
    
    # Парсинг аргументов
    args = parse_arguments()
    
    # Определение URL для парсинга
    urls = args.urls if args.urls else DEFAULT_URLS
    
    # Логируем настройки
    logger.info(f"⚙️ API Host: {API_HOST}:{API_PORT}")
    logger.info(f"🔧 Debug режим: {API_DEBUG}")
    logger.info(f"📋 URL для парсинга: {len(urls)}")
    for i, url in enumerate(urls, 1):
        logger.info(f"  {i}. {url}")
    
    if not urls and args.mode in ["parser", "all"]:
        logger.error("❌ Не указаны URL для парсинга")
        logger.info("💡 Добавьте URL через переменную PARSE_URLS или параметр --urls")
        return
    
    # Установка интервала
    global PARSE_INTERVAL
    PARSE_INTERVAL = args.interval
    
    # Запуск в выбранном режиме
    try:
        if args.mode == "parser":
            await run_parser(urls, not args.once)
        elif args.mode == "api":
            await run_api_server()
        else:  # all
            await run_all(urls)
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)
