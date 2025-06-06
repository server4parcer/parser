#!/usr/bin/env python
"""
Скрипт для настройки базы данных PostgreSQL.

Этот скрипт создает необходимые таблицы и индексы для парсера YCLIENTS.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.logging_config import setup_logging
from config.settings import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
    PG_CONNECTION_STRING, BOOKING_TABLE, URL_TABLE
)


# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)


async def setup_database():
    """Настройка базы данных."""
    logger.info("Настройка базы данных...")
    
    try:
        # Импортируем asyncpg
        import asyncpg
        
        # Подключаемся к серверу PostgreSQL
        logger.info(f"Подключение к серверу PostgreSQL: {DB_HOST}:{DB_PORT}")
        
        # Создаем базу данных, если она не существует
        sys_conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database='postgres'
        )
        
        try:
            # Проверяем существование базы данных
            exists = await sys_conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
                DB_NAME
            )
            
            if not exists:
                logger.info(f"Создание базы данных: {DB_NAME}")
                await sys_conn.execute(f"CREATE DATABASE {DB_NAME}")
            else:
                logger.info(f"База данных {DB_NAME} уже существует")
        finally:
            await sys_conn.close()
        
        # Подключаемся к созданной базе данных
        conn = await asyncpg.connect(PG_CONNECTION_STRING)
        
        try:
            # Проверяем существование таблицы URL
            url_table_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = $1)",
                URL_TABLE
            )
            
            # Создаем таблицу URL, если она не существует
            if not url_table_exists:
                logger.info(f"Создание таблицы {URL_TABLE}")
                await conn.execute(f"""
                    CREATE TABLE {URL_TABLE} (
                        id SERIAL PRIMARY KEY,
                        url TEXT UNIQUE NOT NULL,
                        title TEXT,
                        description TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
            else:
                logger.info(f"Таблица {URL_TABLE} уже существует")
            
            # Проверяем существование таблицы бронирования
            booking_table_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = $1)",
                BOOKING_TABLE
            )
            
            # Создаем таблицу бронирования, если она не существует
            if not booking_table_exists:
                logger.info(f"Создание таблицы {BOOKING_TABLE}")
                await conn.execute(f"""
                    CREATE TABLE {BOOKING_TABLE} (
                        id SERIAL PRIMARY KEY,
                        url_id INTEGER REFERENCES {URL_TABLE}(id),
                        date DATE NOT NULL,
                        time TIME NOT NULL,
                        price TEXT,
                        provider TEXT,
                        seat_number TEXT,
                        extra_data JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(url_id, date, time, seat_number)
                    )
                """)
                
                # Индекс для быстрого поиска по url_id и date
                await conn.execute(f"""
                    CREATE INDEX {BOOKING_TABLE}_url_id_date_idx 
                    ON {BOOKING_TABLE}(url_id, date)
                """)
            else:
                logger.info(f"Таблица {BOOKING_TABLE} уже существует")
            
        finally:
            await conn.close()
        
        logger.info("Настройка базы данных завершена успешно")
    
    except Exception as e:
        logger.error(f"Ошибка при настройке базы данных: {str(e)}")
        raise


async def insert_test_data():
    """Вставка тестовых данных в базу данных."""
    logger.info("Вставка тестовых данных...")
    
    try:
        # Импортируем asyncpg
        import asyncpg
        
        # Подключаемся к базе данных
        conn = await asyncpg.connect(PG_CONNECTION_STRING)
        
        try:
            # Проверяем наличие данных в таблице URL
            url_count = await conn.fetchval(f"SELECT COUNT(*) FROM {URL_TABLE}")
            
            # Вставляем тестовые URL, если таблица пуста
            if url_count == 0:
                logger.info("Вставка тестовых URL")
                
                test_urls = [
                    {
                        "url": "https://yclients.com/company/111111/booking",
                        "title": "Тестовый URL 1",
                        "description": "Тестовый URL для демонстрации работы парсера"
                    },
                    {
                        "url": "https://yclients.com/company/222222/booking",
                        "title": "Тестовый URL 2",
                        "description": "Тестовый URL для демонстрации работы парсера"
                    }
                ]
                
                for test_url in test_urls:
                    await conn.execute(
                        f"""
                        INSERT INTO {URL_TABLE} (url, title, description)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (url) DO NOTHING
                        """,
                        test_url["url"], test_url["title"], test_url["description"]
                    )
            else:
                logger.info(f"В таблице {URL_TABLE} уже есть данные, пропускаем вставку тестовых URL")
        
        finally:
            await conn.close()
        
        logger.info("Вставка тестовых данных завершена успешно")
    
    except Exception as e:
        logger.error(f"Ошибка при вставке тестовых данных: {str(e)}")
        raise


async def main():
    """Основная функция."""
    try:
        # Настраиваем базу данных
        await setup_database()
        
        # Спрашиваем о вставке тестовых данных
        response = input("Желаете вставить тестовые данные в базу данных? (y/N): ")
        
        if response.lower() == 'y':
            await insert_test_data()
        
        print("Настройка базы данных завершена успешно.")
    
    except Exception as e:
        print(f"Ошибка при настройке базы данных: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Запускаем основную функцию
    asyncio.run(main())
