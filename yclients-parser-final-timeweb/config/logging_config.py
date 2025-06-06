"""
Logging Configuration - Настройка системы логирования для парсера YCLIENTS.

Модуль предоставляет функции для настройки системы логирования
с ротацией файлов и оповещениями.
"""
import logging
import logging.config
import os
import sys
from pathlib import Path

from config.settings import LOGGING_CONFIG


def setup_logging() -> None:
    """
    Настройка системы логирования с использованием конфигурации из settings.py.
    """
    # Применяем настройки логирования
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Получаем корневой логгер
    logger = logging.getLogger()
    
    # Устанавливаем обработчик исключений для логирования необработанных исключений
    sys.excepthook = handle_exception


def handle_exception(exc_type, exc_value, exc_traceback) -> None:
    """
    Обработчик исключений для логирования необработанных исключений.
    
    Args:
        exc_type: Тип исключения
        exc_value: Значение исключения
        exc_traceback: Трассировка исключения
    """
    # Игнорируем KeyboardInterrupt, чтобы не перехватывать Ctrl+C
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Получаем логгер
    logger = logging.getLogger()
    
    # Логируем исключение
    logger.error(
        "Необработанное исключение",
        exc_info=(exc_type, exc_value, exc_traceback)
    )


def get_logger(name: str) -> logging.Logger:
    """
    Получение настроенного логгера с указанным именем.
    
    Args:
        name: Имя логгера
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    return logging.getLogger(name)


def add_file_handler(logger: logging.Logger, filepath: str, level: int = logging.INFO) -> None:
    """
    Добавление обработчика файла к логгеру.
    
    Args:
        logger: Логгер
        filepath: Путь к файлу логов
        level: Уровень логирования
    """
    # Создаем директорию для файла логов, если она не существует
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Создаем обработчик файла с ротацией
    handler = logging.handlers.RotatingFileHandler(
        filepath,
        maxBytes=10485760,  # 10 MB
        backupCount=5,
        encoding='utf8'
    )
    
    # Устанавливаем уровень логирования
    handler.setLevel(level)
    
    # Добавляем форматтер
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Добавляем обработчик к логгеру
    logger.addHandler(handler)


def add_email_handler(logger: logging.Logger, email_to: str, level: int = logging.ERROR) -> None:
    """
    Добавление обработчика электронной почты к логгеру.
    
    Args:
        logger: Логгер
        email_to: Адрес электронной почты получателя
        level: Уровень логирования
    """
    # Получаем настройки для отправки email
    email_host = os.environ.get('EMAIL_HOST', 'localhost')
    email_port = int(os.environ.get('EMAIL_PORT', '25'))
    email_from = os.environ.get('EMAIL_FROM', 'yclients-parser@example.com')
    email_subject = os.environ.get('EMAIL_SUBJECT', 'YCLIENTS Parser - Уведомление об ошибке')
    
    # Создаем обработчик SMTP
    handler = logging.handlers.SMTPHandler(
        mailhost=(email_host, email_port),
        fromaddr=email_from,
        toaddrs=[email_to],
        subject=email_subject
    )
    
    # Устанавливаем уровень логирования
    handler.setLevel(level)
    
    # Добавляем форматтер
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Добавляем обработчик к логгеру
    logger.addHandler(handler)


def add_telegram_handler(logger: logging.Logger, token: str, chat_id: str, level: int = logging.ERROR) -> None:
    """
    Добавление обработчика Telegram к логгеру.
    
    Args:
        logger: Логгер
        token: Токен бота Telegram
        chat_id: ID чата Telegram
        level: Уровень логирования
    """
    try:
        # Импортируем библиотеку для работы с Telegram
        import telegram
        
        # Создаем класс обработчика Telegram
        class TelegramHandler(logging.Handler):
            """Обработчик для отправки логов в Telegram."""
            
            def __init__(self, token: str, chat_id: str) -> None:
                """
                Инициализация обработчика.
                
                Args:
                    token: Токен бота Telegram
                    chat_id: ID чата Telegram
                """
                super().__init__()
                self.bot = telegram.Bot(token=token)
                self.chat_id = chat_id
            
            def emit(self, record: logging.LogRecord) -> None:
                """
                Отправка лога в Telegram.
                
                Args:
                    record: Запись лога
                """
                try:
                    message = self.format(record)
                    self.bot.send_message(
                        chat_id=self.chat_id,
                        text=message,
                        parse_mode=telegram.ParseMode.HTML
                    )
                except Exception:
                    self.handleError(record)
        
        # Создаем обработчик Telegram
        handler = TelegramHandler(token, chat_id)
        
        # Устанавливаем уровень логирования
        handler.setLevel(level)
        
        # Добавляем форматтер
        formatter = logging.Formatter('<b>%(levelname)s</b>\n<pre>%(message)s</pre>')
        handler.setFormatter(formatter)
        
        # Добавляем обработчик к логгеру
        logger.addHandler(handler)
    
    except ImportError:
        # Если библиотека telegram не установлена, логируем предупреждение
        logger.warning("Библиотека telegram не установлена. Обработчик Telegram не добавлен.")


def get_module_logger(module_name: str) -> logging.Logger:
    """
    Получение логгера для модуля с настройками по умолчанию.
    
    Args:
        module_name: Имя модуля
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Получаем имя модуля без пути
    name = module_name.split('.')[-1]
    
    # Получаем логгер
    logger = logging.getLogger(f'src.{name}')
    
    return logger


def get_class_logger(cls) -> logging.Logger:
    """
    Получение логгера для класса с настройками по умолчанию.
    
    Args:
        cls: Класс
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Получаем имя модуля и класса
    module_name = cls.__module__
    class_name = cls.__name__
    
    # Получаем логгер
    logger = logging.getLogger(f'{module_name}.{class_name}')
    
    return logger


# Инициализация логирования при импорте модуля
setup_logging()


# Специальный класс для быстрого доступа к логгеру
class Log:
    """Класс для быстрого доступа к логгеру."""
    
    @staticmethod
    def debug(message: str, *args, **kwargs) -> None:
        """
        Логирование сообщения на уровне DEBUG.
        
        Args:
            message: Сообщение
        """
        logging.getLogger().debug(message, *args, **kwargs)
    
    @staticmethod
    def info(message: str, *args, **kwargs) -> None:
        """
        Логирование сообщения на уровне INFO.
        
        Args:
            message: Сообщение
        """
        logging.getLogger().info(message, *args, **kwargs)
    
    @staticmethod
    def warning(message: str, *args, **kwargs) -> None:
        """
        Логирование сообщения на уровне WARNING.
        
        Args:
            message: Сообщение
        """
        logging.getLogger().warning(message, *args, **kwargs)
    
    @staticmethod
    def error(message: str, *args, **kwargs) -> None:
        """
        Логирование сообщения на уровне ERROR.
        
        Args:
            message: Сообщение
        """
        logging.getLogger().error(message, *args, **kwargs)
    
    @staticmethod
    def critical(message: str, *args, **kwargs) -> None:
        """
        Логирование сообщения на уровне CRITICAL.
        
        Args:
            message: Сообщение
        """
        logging.getLogger().critical(message, *args, **kwargs)
    
    @staticmethod
    def exception(message: str, *args, **kwargs) -> None:
        """
        Логирование исключения.
        
        Args:
            message: Сообщение
        """
        logging.getLogger().exception(message, *args, **kwargs)


# Экспортируем все функции и классы
__all__ = [
    'setup_logging',
    'handle_exception',
    'get_logger',
    'add_file_handler',
    'add_email_handler',
    'add_telegram_handler',
    'get_module_logger',
    'get_class_logger',
    'Log'
]
