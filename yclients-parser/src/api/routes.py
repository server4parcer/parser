"""
API Routes - Маршруты и обработчики API для парсера YCLIENTS.

Модуль предоставляет REST API доступ к данным парсера.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, Depends, HTTPException, Query, Path, status, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field

from config.settings import API_KEY
from src.api.auth import get_api_key
from src.database.db_manager import DatabaseManager
from src.parser.yclients_parser import YClientsParser


logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI(
    title="YCLIENTS Parser API",
    description="API для доступа к данным, полученным из YCLIENTS",
    version="1.0.0"
)

# Добавление middleware для CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация базы данных
db_manager = DatabaseManager()

# Модели данных для API
class UrlCreate(BaseModel):
    """Модель для создания нового URL для парсинга."""
    url: HttpUrl
    title: Optional[str] = None
    description: Optional[str] = None


class UrlUpdate(BaseModel):
    """Модель для обновления URL."""
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Url(BaseModel):
    """Модель URL для парсинга."""
    id: int
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool


class BookingData(BaseModel):
    """Модель данных бронирования."""
    id: int
    url: str
    date: str
    time: str
    price: Optional[str] = None
    provider: Optional[str] = None
    seat_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    extra_data: Optional[Dict[str, Any]] = None


class Statistics(BaseModel):
    """Модель статистики парсера."""
    url_count: int
    booking_count: int
    date_stats: List[Dict[str, Any]]
    url_stats: List[Dict[str, Any]]


class ApiResponse(BaseModel):
    """Модель стандартного ответа API."""
    status: str
    message: str
    data: Optional[Any] = None


# События приложения
@app.on_event("startup")
async def startup():
    """Действия при запуске приложения."""
    logger.info("Инициализация API")
    await db_manager.initialize()


@app.on_event("shutdown")
async def shutdown():
    """Действия при остановке приложения."""
    logger.info("Завершение работы API")
    await db_manager.close()


# Маршруты API
@app.get("/", response_model=ApiResponse)
async def read_root():
    """Корневой маршрут API."""
    return ApiResponse(
        status="success",
        message="YCLIENTS Parser API работает",
        data={"version": "1.0.0"}
    )


@app.get("/status", response_model=ApiResponse)
async def get_status(api_key: str = Depends(get_api_key)):
    """
    Получение статуса парсера.
    
    Args:
        api_key: API-ключ для авторизации
    
    Returns:
        ApiResponse: Статус парсера
    """
    try:
        # Получаем статистику
        stats = await db_manager.get_statistics()
        
        return ApiResponse(
            status="success",
            message="Статус парсера получен",
            data=stats
        )
    
    except Exception as e:
        logger.error(f"Ошибка при получении статуса парсера: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении статуса парсера: {str(e)}"
        )


@app.get("/analytics", response_model=ApiResponse)
async def get_analytics(api_key: str = Depends(get_api_key)):
    """
    Получение расширенной бизнес-аналитики.
    
    Args:
        api_key: API-ключ для авторизации
    
    Returns:
        ApiResponse: Бизнес-аналитика
    """
    try:
        # Получаем бизнес-аналитику
        analytics = await db_manager.get_business_analytics()
        
        return ApiResponse(
            status="success",
            message="Бизнес-аналитика получена",
            data=analytics
        )
    
    except Exception as e:
        logger.error(f"Ошибка при получении бизнес-аналитики: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении бизнес-аналитики: {str(e)}"
        )


@app.get("/urls", response_model=ApiResponse)
async def get_urls(
    active_only: bool = Query(False, description="Только активные URL"),
    api_key: str = Depends(get_api_key)
):
    """
    Получение списка URL для парсинга.
    
    Args:
        active_only: Возвращать только активные URL
        api_key: API-ключ для авторизации
    
    Returns:
        ApiResponse: Список URL
    """
    try:
        # Получаем список URL из базы данных
        urls = []
        
        # Здесь будет реализация получения URL
        # Пример:
        async with db_manager.pool.acquire() as conn:
            query = f"SELECT * FROM {db_manager.url_table}"
            if active_only:
                query += " WHERE is_active = TRUE"
            query += " ORDER BY id"
            
            rows = await conn.fetch(query)
            
            urls = [
                {
                    "id": row["id"],
                    "url": row["url"],
                    "title": row["title"],
                    "description": row["description"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    "is_active": row["is_active"]
                }
                for row in rows
            ]
        
        return ApiResponse(
            status="success",
            message=f"Получено {len(urls)} URL",
            data=urls
        )
    
    except Exception as e:
        logger.error(f"Ошибка при получении списка URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка URL: {str(e)}"
        )


@app.post("/urls", response_model=ApiResponse)
async def create_url(
    url_data: UrlCreate,
    api_key: str = Depends(get_api_key)
):
    """
    Создание нового URL для парсинга.
    
    Args:
        url_data: Данные URL
        api_key: API-ключ для авторизации
    
    Returns:
        ApiResponse: Созданный URL
    """
    try:
        # Проверяем, существует ли URL
        async with db_manager.pool.acquire() as conn:
            existing_url = await conn.fetchval(
                f"SELECT id FROM {db_manager.url_table} WHERE url = $1",
                str(url_data.url)
            )
            
            if existing_url:
                return ApiResponse(
                    status="error",
                    message="URL уже существует",
                    data={"id": existing_url}
                )
            
            # Создаем новый URL
            url_id = await conn.fetchval(
                f"""
                INSERT INTO {db_manager.url_table} (url, title, description, is_active)
                VALUES ($1, $2, $3, TRUE)
                RETURNING id
                """,
                str(url_data.url), url_data.title, url_data.description
            )
            
            # Получаем созданный URL
            row = await conn.fetchrow(
                f"SELECT * FROM {db_manager.url_table} WHERE id = $1",
                url_id
            )
            
            created_url = {
                "id": row["id"],
                "url": row["url"],
                "title": row["title"],
                "description": row["description"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                "is_active": row["is_active"]
            }
        
        return ApiResponse(
            status="success",
            message="URL успешно создан",
            data=created_url
        )
    
    except Exception as e:
        logger.error(f"Ошибка при создании URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании URL: {str(e)}"
        )


@app.get("/urls/{url_id}", response_model=ApiResponse)
async def get_url(
    url_id: int = Path(..., description="ID URL"),
    api_key: str = Depends(get_api_key)
):
    """
    Получение информации о URL.
    
    Args:
        url_id: ID URL
        api_key: API-ключ для авторизации
    
    Returns:
        ApiResponse: Информация о URL
    """
    try:
        # Получаем URL из базы данных
        async with db_manager.pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT * FROM {db_manager.url_table} WHERE id = $1",
                url_id
            )
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"URL с ID {url_id} не найден"
                )
            
            url_data = {
                "id": row["id"],
                "url": row["url"],
                "title": row["title"],
                "description": row["description"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                "is_active": row["is_active"]
            }
        
        return ApiResponse(
            status="success",
            message=f"URL с ID {url_id} получен",
            data=url_data
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Ошибка при получении URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении URL: {str(e)}"
        )


@app.put("/urls/{url_id}", response_model=ApiResponse)
async def update_url(
    url_id: int = Path(..., description="ID URL"),
    url_data: UrlUpdate = None,
    api_key: str = Depends(get_api_key)
):
    """
    Обновление информации о URL.
    
    Args:
        url_id: ID URL
        url_data: Данные для обновления
        api_key: API-ключ для авторизации
    
    Returns:
        ApiResponse: Обновленная информация о URL
    """
    try:
        # Проверяем, существует ли URL
        async with db_manager.pool.acquire() as conn:
            existing_url = await conn.fetchrow(
                f"SELECT * FROM {db_manager.url_table} WHERE id = $1",
                url_id
            )
            
            if not existing_url:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"URL с ID {url_id} не найден"
                )
            
            # Формируем запрос на обновление
            update_fields = []
            update_values = []
            
            if url_data.title is not None:
                update_fields.append("title = $" + str(len(update_values) + 1))
                update_values.append(url_data.title)
            
            if url_data.description is not None:
                update_fields.append("description = $" + str(len(update_values) + 1))
                update_values.append(url_data.description)
            
            if url_data.is_active is not None:
                update_fields.append("is_active = $" + str(len(update_values) + 1))
                update_values.append(url_data.is_active)
            
            if not update_fields:
                # Если нет полей для обновления, возвращаем текущие данные
                url_data = {
                    "id": existing_url["id"],
                    "url": existing_url["url"],
                    "title": existing_url["title"],
                    "description": existing_url["description"],
                    "created_at": existing_url["created_at"].isoformat() if existing_url["created_at"] else None,
                    "updated_at": existing_url["updated_at"].isoformat() if existing_url["updated_at"] else None,
                    "is_active": existing_url["is_active"]
                }
                
                return ApiResponse(
                    status="success",
                    message="URL не был изменен",
                    data=url_data
                )
            
            # Добавляем обновление поля updated_at
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            # Обновляем URL
            query = f"""
                UPDATE {db_manager.url_table}
                SET {', '.join(update_fields)}
                WHERE id = ${len(update_values) + 1}
                RETURNING *
            """
            update_values.append(url_id)
            
            updated_row = await conn.fetchrow(query, *update_values)
            
            updated_url = {
                "id": updated_row["id"],
                "url": updated_row["url"],
                "title": updated_row["title"],
                "description": updated_row["description"],
                "created_at": updated_row["created_at"].isoformat() if updated_row["created_at"] else None,
                "updated_at": updated_row["updated_at"].isoformat() if updated_row["updated_at"] else None,
                "is_active": updated_row["is_active"]
            }
        
        return ApiResponse(
            status="success",
            message=f"URL с ID {url_id} успешно обновлен",
            data=updated_url
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Ошибка при обновлении URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении URL: {str(e)}"
        )


@app.delete("/urls/{url_id}", response_model=ApiResponse)
async def delete_url(
    url_id: int = Path(..., description="ID URL"),
    api_key: str = Depends(get_api_key)
):
    """
    Удаление URL.
    
    Args:
        url_id: ID URL
        api_key: API-ключ для авторизации
    
    Returns:
        ApiResponse: Статус операции
    """
    try:
        # Проверяем, существует ли URL
        async with db_manager.pool.acquire() as conn:
            existing_url = await conn.fetchval(
                f"SELECT id FROM {db_manager.url_table} WHERE id = $1",
                url_id
            )
            
            if not existing_url:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"URL с ID {url_id} не найден"
                )
            
            # Удаляем связанные данные бронирования
            await conn.execute(
                f"DELETE FROM {db_manager.booking_table} WHERE url_id = $1",
                url_id
            )
            
            # Удаляем URL
            await conn.execute(
                f"DELETE FROM {db_manager.url_table} WHERE id = $1",
                url_id
            )
        
        return ApiResponse(
            status="success",
            message=f"URL с ID {url_id} успешно удален",
            data=None
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Ошибка при удалении URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении URL: {str(e)}"
        )


@app.get("/data", response_model=ApiResponse)
async def get_booking_data(
    url_id: Optional[int] = Query(None, description="ID URL"),
    url: Optional[str] = Query(None, description="URL страницы"),
    date_from: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    location_name: Optional[str] = Query(None, description="Название местоположения"),
    court_type: Optional[str] = Query(None, description="Тип корта (TENNIS, BASKETBALL, etc.)"),
    time_category: Optional[str] = Query(None, description="Категория времени (DAY, EVENING, WEEKEND)"),
    limit: int = Query(100, description="Максимальное количество записей"),
    offset: int = Query(0, description="Смещение"),
    api_key: str = Depends(get_api_key)
):
    """
    Получение данных бронирования.
    
    Args:
        url_id: ID URL
        url: URL страницы
        date_from: Начальная дата
        date_to: Конечная дата
        limit: Максимальное количество записей
        offset: Смещение
        api_key: API-ключ для авторизации
    
    Returns:
        ApiResponse: Данные бронирования
    """
    try:
        # Формируем запрос
        query = f"""
            SELECT b.id, u.url, b.date, b.time, b.price, b.provider, b.seat_number, 
                b.location_name, b.court_type, b.time_category, b.duration, 
                b.review_count, b.prepayment_required, b.raw_venue_data,
                b.extra_data, b.created_at, b.updated_at
            FROM {db_manager.booking_table} b
            JOIN {db_manager.url_table} u ON b.url_id = u.id
            WHERE 1=1
        """
        params = []
        
        # Добавляем фильтры
        if url_id:
            query += f" AND u.id = ${len(params) + 1}"
            params.append(url_id)
        
        if url:
            query += f" AND u.url = ${len(params) + 1}"
            params.append(url)
        
        if date_from:
            query += f" AND b.date >= ${len(params) + 1}"
            params.append(date_from)
        
        if date_to:
            query += f" AND b.date <= ${len(params) + 1}"
            params.append(date_to)
            
        # Новые фильтры бизнес-аналитики
        if location_name:
            query += f" AND b.location_name = ${len(params) + 1}"
            params.append(location_name)
            
        if court_type:
            query += f" AND b.court_type = ${len(params) + 1}"
            params.append(court_type)
            
        if time_category:
            query += f" AND b.time_category = ${len(params) + 1}"
            params.append(time_category)
        
        # Получаем общее количество записей
        count_query = f"SELECT COUNT(*) FROM ({query}) AS count_query"
        
        # Добавляем сортировку, лимит и смещение
        query += f" ORDER BY b.date DESC, b.time DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])
        
        # Выполняем запрос
        async with db_manager.pool.acquire() as conn:
            # Получаем общее количество записей
            total_count = await conn.fetchval(count_query, *params[:-2])
            
            # Получаем данные
            rows = await conn.fetch(query, *params)
            
            # Преобразуем результаты
            booking_data = []
            for row in rows:
                data = {
                    "id": row["id"],
                    "url": row["url"],
                    "date": row["date"].isoformat(),
                    "time": row["time"].isoformat(),
                    "price": row["price"],
                    "provider": row["provider"],
                    "seat_number": row["seat_number"],
                    "location_name": row["location_name"],
                    "court_type": row["court_type"],
                    "time_category": row["time_category"],
                    "duration": row["duration"],
                    "review_count": row["review_count"],
                    "prepayment_required": row["prepayment_required"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
                }
                
                # Add raw venue data if it exists
                if row["raw_venue_data"]:
                    data["raw_venue_data"] = json.loads(row["raw_venue_data"]) if isinstance(row["raw_venue_data"], str) else row["raw_venue_data"]
                
                # Добавляем дополнительные данные
                if row["extra_data"]:
                    extra_data = json.loads(row["extra_data"])
                    for key, value in extra_data.items():
                        if key not in data:
                            data[key] = value
                
                booking_data.append(data)
        
        return ApiResponse(
            status="success",
            message=f"Получено {len(booking_data)} записей бронирования",
            data={
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "items": booking_data
            }
        )
    
    except Exception as e:
        logger.error(f"Ошибка при получении данных бронирования: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении данных бронирования: {str(e)}"
        )


@app.get("/export", response_model=ApiResponse)
async def export_data(
    background_tasks: BackgroundTasks,
    format: str = Query("csv", description="Формат экспорта (csv, json)"),
    url_id: Optional[int] = Query(None, description="ID URL"),
    url: Optional[str] = Query(None, description="URL страницы"),
    date_from: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    location_name: Optional[str] = Query(None, description="Название местоположения"),
    court_type: Optional[str] = Query(None, description="Тип корта (TENNIS, BASKETBALL, etc.)"),
    time_category: Optional[str] = Query(None, description="Категория времени (DAY, EVENING, WEEKEND)"),
    include_analytics: Optional[bool] = Query(False, description="Включить аналитические данные"),
    api_key: str = Depends(get_api_key)
):
    """
    Экспорт данных бронирования в файл.
    
    Args:
        background_tasks: Задачи в фоне
        format: Формат экспорта (csv, json)
        url_id: ID URL
        url: URL страницы
        date_from: Начальная дата
        date_to: Конечная дата
        api_key: API-ключ для авторизации
    
    Returns:
        ApiResponse: Информация о созданном файле
    """
    try:
        # Проверяем формат
        if format.lower() not in ["csv", "json"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неподдерживаемый формат экспорта. Поддерживаемые форматы: csv, json"
            )
        
        # Создаем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"booking_data_{timestamp}.{format.lower()}"
        
        # Путь к файлу
        filepath = os.path.join(db_manager.export_path, filename)
        
        # Получаем URL для запроса
        request_url = None
        if url:
            request_url = url
        elif url_id:
            async with db_manager.pool.acquire() as conn:
                request_url = await conn.fetchval(
                    f"SELECT url FROM {db_manager.url_table} WHERE id = $1",
                    url_id
                )
        
        # Экспортируем данные
        if format.lower() == "csv":
            filepath = await db_manager.export_to_csv(
                filepath, request_url, date_from, date_to,
                location_name, court_type, time_category, include_analytics
            )
        else:
            filepath = await db_manager.export_to_json(
                filepath, request_url, date_from, date_to,
                location_name, court_type, time_category, include_analytics
            )
        
        if not filepath:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при экспорте данных"
            )
        
        # Добавляем задачу на удаление файла через 24 часа
        background_tasks.add_task(delete_file_after_delay, filepath, 86400)  # 24 часа = 86400 секунд
        
        return ApiResponse(
            status="success",
            message=f"Данные успешно экспортированы в {format.upper()}",
            data={
                "filename": os.path.basename(filepath),
                "url": f"/download/{os.path.basename(filepath)}",
                "expires_in": "24 часа"
            }
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Ошибка при экспорте данных: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при экспорте данных: {str(e)}"
        )


@app.get("/analytics/pricing", response_model=ApiResponse)
async def get_price_analytics(
    court_type: Optional[str] = Query(None, description="Тип корта (TENNIS, BASKETBALL, etc.)"),
    time_category: Optional[str] = Query(None, description="Категория времени (DAY, EVENING, WEEKEND)"),
    location: Optional[str] = Query(None, description="Название местоположения"),
    time_frame: Optional[str] = Query("last_30_days", description="Временной период (last_7_days, last_30_days, last_90_days)"),
    api_key: str = Depends(get_api_key)
):
    """
    Получение аналитики цен по кортам.
    
    Args:
        court_type: Фильтр по типу корта
        time_category: Фильтр по категории времени
        location: Фильтр по местоположению
        time_frame: Временной период
        api_key: API-ключ для авторизации
    
    Returns:
        ApiResponse: Аналитические данные по ценам
    """
    try:
        # Получаем аналитические данные
        price_ranges = None
        price_comparison = None
        
        async with db_manager.pool.acquire() as conn:
            # Получаем диапазоны цен по типу корта
            query, params = BookingQueries.get_price_ranges_by_court_type()
            price_ranges = await conn.fetch(query, *params)
            
            # Получаем сравнение цен по категориям времени
            query, params = BookingQueries.get_price_comparison_by_time_category()
            price_comparison = await conn.fetch(query, *params)
        
        # Преобразуем результаты
        price_ranges_data = []
        for row in price_ranges:
            if court_type and row["court_type"] != court_type:
                continue
                
            price_ranges_data.append({
                "court_type": row["court_type"],
                "min_price": row["min_price"],
                "max_price": row["max_price"],
                "avg_price": float(row["avg_price"]),
                "venue_count": row["venue_count"]
            })
        
        price_comparison_data = []
        for row in price_comparison:
            if court_type and row["court_type"] != court_type:
                continue
                
            if time_category and row["time_category"] != time_category:
                continue
                
            price_comparison_data.append({
                "court_type": row["court_type"],
                "time_category": row["time_category"],
                "avg_price": float(row["avg_price"]),
                "slot_count": row["slot_count"]
            })
        
        return ApiResponse(
            status="success",
            message="Получены аналитические данные по ценам",
            data={
                "price_ranges": price_ranges_data,
                "price_comparison": price_comparison_data
            }
        )
    
    except Exception as e:
        logger.error(f"Ошибка при получении аналитики цен: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении аналитики цен: {str(e)}"
        )


@app.get("/analytics/availability", response_model=ApiResponse)
async def get_availability_analytics(
    court_type: Optional[str] = Query(None, description="Тип корта (TENNIS, BASKETBALL, etc.)"),
    location: Optional[str] = Query(None, description="Название местоположения"),
    time_frame: Optional[str] = Query("last_30_days", description="Временной период (last_7_days, last_30_days, last_90_days)"),
    api_key: str = Depends(get_api_key)
):
    """
    Получение аналитики доступности.
    
    Args:
        court_type: Фильтр по типу корта
        location: Фильтр по местоположению
        time_frame: Временной период
        api_key: API-ключ для авторизации
    
    Returns:
        ApiResponse: Аналитические данные по доступности
    """
    try:
        # Получаем аналитические данные
        availability_by_location = None
        court_types_by_venue = None
        
        async with db_manager.pool.acquire() as conn:
            # Получаем доступность по местоположению
            query, params = BookingQueries.get_availability_by_location()
            availability_by_location = await conn.fetch(query, *params)
            
            # Получаем типы кортов по площадке
            query, params = BookingQueries.get_court_types_by_venue()
            court_types_by_venue = await conn.fetch(query, *params)
        
        # Преобразуем результаты
        availability_data = []
        for row in availability_by_location:
            if location and row["location_name"] != location:
                continue
                
            availability_data.append({
                "location_name": row["location_name"],
                "date": row["date"].isoformat(),
                "total_slots": row["total_slots"]
            })
        
        venue_data = []
        for row in court_types_by_venue:
            if court_type and row["court_type"] != court_type:
                continue
                
            if location and row["location_name"] != location:
                continue
                
            venue_data.append({
                "url": row["url"],
                "location_name": row["location_name"],
                "court_type": row["court_type"],
                "slot_count": row["slot_count"]
            })
        
        return ApiResponse(
            status="success",
            message="Получены аналитические данные по доступности",
            data={
                "availability": availability_data,
                "venues": venue_data
            }
        )
    
    except Exception as e:
        logger.error(f"Ошибка при получении аналитики доступности: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении аналитики доступности: {str(e)}"
        )


@app.get("/analytics/price_history", response_model=ApiResponse)
async def get_price_history_analytics(
    venue_id: Optional[int] = Query(None, description="ID площадки"),
    court_type: Optional[str] = Query(None, description="Тип корта (TENNIS, BASKETBALL, etc.)"),
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    days: Optional[int] = Query(30, description="Количество дней для анализа"),
    api_key: str = Depends(get_api_key)
):
    """
    Получение аналитики изменения цен.
    
    Args:
        venue_id: ID площадки
        court_type: Фильтр по типу корта
        start_date: Начальная дата
        days: Количество дней для анализа
        api_key: API-ключ для авторизации
    
    Returns:
        ApiResponse: Аналитические данные по изменению цен
    """
    try:
        # Получаем аналитические данные
        price_changes = None
        
        async with db_manager.pool.acquire() as conn:
            # Получаем изменения цен
            query, params = PriceHistoryQueries.get_price_changes(days)
            price_changes = await conn.fetch(query, *params)
        
        # Преобразуем результаты
        price_history_data = []
        for row in price_changes:
            if court_type and row["court_type"] != court_type:
                continue
                
            price_history_data.append({
                "id": row["id"],
                "current_price": row["current_price"],
                "historical_price": row["historical_price"],
                "recorded_at": row["recorded_at"].isoformat(),
                "court_type": row["court_type"],
                "location_name": row["location_name"],
                "time_category": row["time_category"],
                "url": row["url"]
            })
        
        return ApiResponse(
            status="success",
            message="Получены аналитические данные по изменению цен",
            data={
                "price_history": price_history_data
            }
        )
    
    except Exception as e:
        logger.error(f"Ошибка при получении аналитики изменения цен: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении аналитики изменения цен: {str(e)}"
        )


@app.get("/download/{filename}")
async def download_file(
    filename: str = Path(..., description="Имя файла"),
    api_key: str = Depends(get_api_key)
):
    """
    Скачивание файла.
    
    Args:
        filename: Имя файла
        api_key: API-ключ для авторизации
    
    Returns:
        FileResponse: Файл для скачивания
    """
    try:
        # Проверяем, существует ли файл
        filepath = os.path.join(db_manager.export_path, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Файл {filename} не найден"
            )
        
        # Определяем MIME-тип
        content_type = "text/csv" if filename.endswith(".csv") else "application/json"
        
        # Отправляем файл
        return FileResponse(
            filepath,
            media_type=content_type,
            filename=filename
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Ошибка при скачивании файла: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при скачивании файла: {str(e)}"
        )


@app.post("/parse", response_model=ApiResponse)
async def run_parser(
    background_tasks: BackgroundTasks,
    url_id: Optional[int] = Query(None, description="ID URL для парсинга"),
    url: Optional[str] = Query(None, description="URL для парсинга"),
    api_key: str = Depends(get_api_key)
):
    """
    Запуск парсера для указанного URL.
    
    Args:
        background_tasks: Задачи в фоне
        url_id: ID URL для парсинга
        url: URL для парсинга
        api_key: API-ключ для авторизации
    
    Returns:
        ApiResponse: Статус операции
    """
    try:
        # Получаем URL для парсинга
        if not url and not url_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Необходимо указать url или url_id"
            )
        
        parse_url = url
        
        if not parse_url and url_id:
            async with db_manager.pool.acquire() as conn:
                parse_url = await conn.fetchval(
                    f"SELECT url FROM {db_manager.url_table} WHERE id = $1",
                    url_id
                )
        
        if not parse_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"URL с ID {url_id} не найден"
            )
        
        # Запускаем парсер в фоновом режиме
        background_tasks.add_task(run_parser_task, parse_url)
        
        return ApiResponse(
            status="success",
            message=f"Парсер запущен для {parse_url}",
            data=None
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Ошибка при запуске парсера: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при запуске парсера: {str(e)}"
        )


@app.post("/parse/all", response_model=ApiResponse)
async def run_parser_for_all(
    background_tasks: BackgroundTasks,
    active_only: bool = Query(True, description="Только активные URL"),
    api_key: str = Depends(get_api_key)
):
    """
    Запуск парсера для всех URL.
    
    Args:
        background_tasks: Задачи в фоне
        active_only: Только активные URL
        api_key: API-ключ для авторизации
    
    Returns:
        ApiResponse: Статус операции
    """
    try:
        # Получаем список URL из базы данных
        urls = []
        
        async with db_manager.pool.acquire() as conn:
            query = f"SELECT url FROM {db_manager.url_table}"
            if active_only:
                query += " WHERE is_active = TRUE"
            
            rows = await conn.fetch(query)
            urls = [row["url"] for row in rows]
        
        if not urls:
            return ApiResponse(
                status="warning",
                message="Нет URL для парсинга",
                data=None
            )
        
        # Запускаем парсер для всех URL в фоновом режиме
        background_tasks.add_task(run_parser_task_for_all, urls)
        
        return ApiResponse(
            status="success",
            message=f"Парсер запущен для {len(urls)} URL",
            data={"count": len(urls)}
        )
    
    except Exception as e:
        logger.error(f"Ошибка при запуске парсера для всех URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при запуске парсера для всех URL: {str(e)}"
        )


# Вспомогательные функции
async def delete_file_after_delay(filepath: str, delay_seconds: int) -> None:
    """
    Удаление файла после указанной задержки.
    
    Args:
        filepath: Путь к файлу
        delay_seconds: Задержка в секундах
    """
    try:
        # Ждем указанное время
        await asyncio.sleep(delay_seconds)
        
        # Проверяем, существует ли файл
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Файл {filepath} удален")
    
    except Exception as e:
        logger.error(f"Ошибка при удалении файла {filepath}: {str(e)}")


async def run_parser_task(url: str) -> None:
    """
    Задача для запуска парсера.
    
    Args:
        url: URL для парсинга
    """
    try:
        logger.info(f"Запуск парсера для {url}")
        
        # Создаем экземпляр парсера
        parser = YClientsParser([url], db_manager)
        
        # Запускаем одну итерацию парсинга
        await parser.run_single_iteration()
        
        logger.info(f"Парсинг завершен для {url}")
    
    except Exception as e:
        logger.error(f"Ошибка при выполнении парсинга {url}: {str(e)}")


async def run_parser_task_for_all(urls: List[str]) -> None:
    """
    Задача для запуска парсера для всех URL.
    
    Args:
        urls: Список URL для парсинга
    """
    try:
        logger.info(f"Запуск парсера для {len(urls)} URL")
        
        # Создаем экземпляр парсера
        parser = YClientsParser(urls, db_manager)
        
        # Запускаем одну итерацию парсинга
        await parser.run_single_iteration()
        
        logger.info(f"Парсинг завершен для {len(urls)} URL")
    
    except Exception as e:
        logger.error(f"Ошибка при выполнении парсинга для всех URL: {str(e)}")
