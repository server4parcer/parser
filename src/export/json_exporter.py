"""
JSON Exporter - Модуль для экспорта данных в формате JSON.

Модуль предоставляет функции для экспорта данных бронирования в JSON-файл.
"""
import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.database.models import BookingData


logger = logging.getLogger(__name__)


class JsonEncoder(json.JSONEncoder):
    """Кастомный JSON энкодер для обработки типов данных Python."""
    
    def default(self, obj):
        # Обработка datetime
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Обработка множеств
        if isinstance(obj, set):
            return list(obj)
        
        # Стандартная обработка для остальных типов
        return json.JSONEncoder.default(self, obj)


class JsonExporter:
    """Класс для экспорта данных в формате JSON."""
    
    @staticmethod
    async def export_booking_data(
        filepath: str,
        booking_data: List[Dict[str, Any]],
        pretty_print: bool = True
    ) -> str:
        """
        Экспорт данных бронирования в JSON-файл.
        
        Args:
            filepath: Путь к файлу
            booking_data: Данные бронирования
            pretty_print: Форматированный вывод JSON
            
        Returns:
            str: Путь к созданному файлу
        """
        try:
            logger.info(f"Экспорт {len(booking_data)} записей в JSON: {filepath}")
            
            # Если данных нет, возвращаем пустую строку
            if not booking_data:
                logger.warning("Нет данных для экспорта в JSON")
                return ""
            
            # Создаем директорию, если она не существует
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Преобразуем данные в список словарей
            data_to_export = []
            for item in booking_data:
                # Если item является экземпляром BookingData, преобразуем его в словарь
                if isinstance(item, BookingData):
                    item = item.to_dict()
                
                data_to_export.append(item)
            
            # Экспортируем данные в JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                if pretty_print:
                    json.dump(data_to_export, f, cls=JsonEncoder, ensure_ascii=False, indent=2)
                else:
                    json.dump(data_to_export, f, cls=JsonEncoder, ensure_ascii=False)
            
            logger.info(f"Данные успешно экспортированы в JSON: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Ошибка при экспорте данных в JSON: {str(e)}")
            return ""
    
    @staticmethod
    async def export_urls(
        filepath: str,
        urls: List[Dict[str, Any]],
        pretty_print: bool = True
    ) -> str:
        """
        Экспорт URL в JSON-файл.
        
        Args:
            filepath: Путь к файлу
            urls: Список URL
            pretty_print: Форматированный вывод JSON
            
        Returns:
            str: Путь к созданному файлу
        """
        try:
            logger.info(f"Экспорт {len(urls)} URL в JSON: {filepath}")
            
            # Если данных нет, возвращаем пустую строку
            if not urls:
                logger.warning("Нет данных для экспорта в JSON")
                return ""
            
            # Создаем директорию, если она не существует
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Экспортируем данные в JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                if pretty_print:
                    json.dump(urls, f, cls=JsonEncoder, ensure_ascii=False, indent=2)
                else:
                    json.dump(urls, f, cls=JsonEncoder, ensure_ascii=False)
            
            logger.info(f"URL успешно экспортированы в JSON: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Ошибка при экспорте URL в JSON: {str(e)}")
            return ""
    
    @staticmethod
    async def export_statistics(
        filepath: str,
        statistics: Dict[str, Any],
        pretty_print: bool = True
    ) -> str:
        """
        Экспорт статистики в JSON-файл.
        
        Args:
            filepath: Путь к файлу
            statistics: Статистика
            pretty_print: Форматированный вывод JSON
            
        Returns:
            str: Путь к созданному файлу
        """
        try:
            logger.info(f"Экспорт статистики в JSON: {filepath}")
            
            # Создаем директорию, если она не существует
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Экспортируем данные в JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                if pretty_print:
                    json.dump(statistics, f, cls=JsonEncoder, ensure_ascii=False, indent=2)
                else:
                    json.dump(statistics, f, cls=JsonEncoder, ensure_ascii=False)
            
            logger.info(f"Статистика успешно экспортирована в JSON: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Ошибка при экспорте статистики в JSON: {str(e)}")
            return ""
