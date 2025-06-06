"""
CSV Exporter - Модуль для экспорта данных в формате CSV.

Модуль предоставляет функции для экспорта данных бронирования в CSV-файл.
"""
import csv
import logging
import os
from typing import Dict, List, Optional, Any

from src.database.models import BookingData


logger = logging.getLogger(__name__)


class CsvExporter:
    """Класс для экспорта данных в формате CSV."""
    
    @staticmethod
    async def export_booking_data(
        filepath: str,
        booking_data: List[Dict[str, Any]],
        headers: Optional[List[str]] = None
    ) -> str:
        """
        Экспорт данных бронирования в CSV-файл.
        
        Args:
            filepath: Путь к файлу
            booking_data: Данные бронирования
            headers: Заголовки столбцов (опционально)
            
        Returns:
            str: Путь к созданному файлу
        """
        try:
            logger.info(f"Экспорт {len(booking_data)} записей в CSV: {filepath}")
            
            # Если данных нет, возвращаем пустую строку
            if not booking_data:
                logger.warning("Нет данных для экспорта в CSV")
                return ""
            
            # Создаем директорию, если она не существует
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Определяем заголовки, если они не указаны
            if not headers:
                # Собираем все ключи из всех записей
                all_keys = set()
                for item in booking_data:
                    all_keys.update(item.keys())
                
                # Приоритетные ключи (они будут первыми в CSV)
                priority_keys = [
                    'id', 'url', 'date', 'time', 'price', 'provider', 'seat_number',
                    'created_at', 'updated_at'
                ]
                
                # Сортируем заголовки: сначала приоритетные, затем остальные в алфавитном порядке
                headers = []
                for key in priority_keys:
                    if key in all_keys:
                        headers.append(key)
                        all_keys.remove(key)
                
                headers.extend(sorted(all_keys))
            
            # Экспортируем данные в CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                
                for item in booking_data:
                    # Если item является экземпляром BookingData, преобразуем его в словарь
                    if isinstance(item, BookingData):
                        item = item.to_dict()
                    
                    # Записываем только поля, указанные в заголовках
                    row = {k: item.get(k, '') for k in headers}
                    writer.writerow(row)
            
            logger.info(f"Данные успешно экспортированы в CSV: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Ошибка при экспорте данных в CSV: {str(e)}")
            return ""
    
    @staticmethod
    async def export_urls(
        filepath: str,
        urls: List[Dict[str, Any]],
        headers: Optional[List[str]] = None
    ) -> str:
        """
        Экспорт URL в CSV-файл.
        
        Args:
            filepath: Путь к файлу
            urls: Список URL
            headers: Заголовки столбцов (опционально)
            
        Returns:
            str: Путь к созданному файлу
        """
        try:
            logger.info(f"Экспорт {len(urls)} URL в CSV: {filepath}")
            
            # Если данных нет, возвращаем пустую строку
            if not urls:
                logger.warning("Нет данных для экспорта в CSV")
                return ""
            
            # Создаем директорию, если она не существует
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Определяем заголовки, если они не указаны
            if not headers:
                headers = ['id', 'url', 'title', 'description', 'created_at', 'updated_at', 'is_active']
            
            # Экспортируем данные в CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                
                for url in urls:
                    # Записываем только поля, указанные в заголовках
                    row = {k: url.get(k, '') for k in headers}
                    writer.writerow(row)
            
            logger.info(f"URL успешно экспортированы в CSV: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Ошибка при экспорте URL в CSV: {str(e)}")
            return ""
