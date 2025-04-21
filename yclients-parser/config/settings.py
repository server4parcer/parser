"""
Settings - Конфигурационные параметры для парсера YCLIENTS.

Модуль содержит все настройки, используемые в приложении.
"""
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Основные пути
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
EXPORT_PATH = DATA_DIR / "export"

# Создаем необходимые директории
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(EXPORT_PATH, exist_ok=True)

# Настройки парсера
PARSE_INTERVAL = 600  # Интервал обновления данных в секундах (10 минут)
MAX_RETRIES = 3  # Максимальное количество попыток парсинга
TIMEOUT = 30000  # Таймаут ожидания элементов в мс
PAGE_LOAD_TIMEOUT = 60000  # Таймаут загрузки страницы в мс

# Настройки Playwright
BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-site-isolation-trials",
    "--disable-web-security",
    "--disable-features=TranslateUI",
    "--disable-notifications",
    "--no-first-run",
    "--no-default-browser-check",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-popup-blocking",
    "--ignore-certificate-errors",
    "--enable-features=NetworkService"
]

# Масштабирование и прокси
MAX_CONCURRENT_TASKS = 5  # Максимальное количество одновременных задач
MAX_BROWSER_INSTANCES = 3  # Максимальное количество экземпляров браузера

# URL для парсинга (пример, будет загружаться из базы данных или переменных окружения)
DEFAULT_URLS = []

# Настройки User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62"
]

# Настройки размеров окна
VIEWPORT_SIZES = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720}
]

# Настройки базы данных
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "yclients_parser")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

# Строка подключения к базе данных
PG_CONNECTION_STRING = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Названия таблиц
BOOKING_TABLE = "booking_data"
URL_TABLE = "urls"

# Настройки Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Настройки прокси
PROXY_LIST_PATH = os.path.join(DATA_DIR, "proxies.json")
PROXY_CHECK_URL = "https://www.google.com"
PROXY_TIMEOUT = 10  # Таймаут подключения к прокси в секундах
PROXY_CHECK_INTERVAL = 3600  # Интервал проверки прокси в секундах (1 час)
MAX_FAILED_ATTEMPTS = 3  # Максимальное количество неудачных попыток использования прокси

# Загрузка переменных окружения из .env файла
try:
    from dotenv import load_dotenv
    
    env_path = BASE_DIR / ".env"
    load_dotenv(env_path)
    
    # Обновляем значения из переменных окружения
    SUPABASE_URL = os.environ.get("SUPABASE_URL", SUPABASE_URL)
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", SUPABASE_KEY)
    
    DB_HOST = os.environ.get("DB_HOST", DB_HOST)
    DB_PORT = os.environ.get("DB_PORT", DB_PORT)
    DB_NAME = os.environ.get("DB_NAME", DB_NAME)
    DB_USER = os.environ.get("DB_USER", DB_USER)
    DB_PASSWORD = os.environ.get("DB_PASSWORD", DB_PASSWORD)
    
    # Обновляем строку подключения
    PG_CONNECTION_STRING = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Загрузка URL для парсинга из переменных окружения
    url_env = os.environ.get("PARSE_URLS", "")
    if url_env:
        DEFAULT_URLS = [url.strip() for url in url_env.split(",") if url.strip()]
    
except ImportError:
    pass  # dotenv не установлен, используем значения по умолчанию

# Настройки логирования
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "simple": {
            "format": "%(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "verbose",
            "filename": os.path.join(LOGS_DIR, "parser.log"),
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
            "encoding": "utf8",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "verbose",
            "filename": os.path.join(LOGS_DIR, "error.log"),
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
            "encoding": "utf8",
        },
    },
    "loggers": {
        "": {  # Корневой логгер
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": True,
        },
        "src": {
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "playwright": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# Функция для загрузки URL из файла
def load_urls_from_file() -> List[str]:
    """
    Загрузка списка URL из файла.
    
    Returns:
        List[str]: Список URL для парсинга
    """
    urls_file = os.path.join(DATA_DIR, "urls.txt")
    if os.path.exists(urls_file):
        with open(urls_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

# Загружаем URL из файла, если они не определены
if not DEFAULT_URLS:
    DEFAULT_URLS = load_urls_from_file()

# API-настройки
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8000"))
API_DEBUG = os.environ.get("API_DEBUG", "False").lower() in ("true", "1", "t")
API_KEY = os.environ.get("API_KEY", "yclients_parser_api_key")
