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
        try:
            if active_only:
                response = db_manager.supabase.table(db_manager.url_table).select("*").eq("is_active", True).order("id").execute()
            else:
                response = db_manager.supabase.table(db_manager.url_table).select("*").order("id").execute()
            
            rows = response.data or []
            
            urls = [
                {
                    "id": row["id"],
                    "url": row["url"],
                    "title": row.get("title"),
                    "description": row.get("description"),
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("updated_at"),
                    "is_active": row.get("is_active", True)
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Ошибка получения URL из Supabase: {str(e)}")
            urls = []
        
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
        try:
            response = db_manager.supabase.table(db_manager.url_table).select("id").eq("url", str(url_data.url)).execute()
            
            if response.data:
                return ApiResponse(
                    status="error",
                    message="URL уже существует",
                    data={"id": response.data[0]["id"]}
                )
            
            # Создаем новый URL (только обязательное поле url, т.к. в таблице минимальная схема)
            insert_data = {
                "url": str(url_data.url)
            }
            
            response = db_manager.supabase.table(db_manager.url_table).insert(insert_data).execute()
            
            if response.data:
                created_url = {
                    "id": response.data[0]["id"],
                    "url": response.data[0]["url"],
                    "title": response.data[0].get("title"),
                    "description": response.data[0].get("description"),
                    "created_at": response.data[0].get("created_at"),
                    "updated_at": response.data[0].get("updated_at"),
                    "is_active": response.data[0].get("is_active", True)
                }
            else:
                raise Exception("Ошибка создания URL")
            
        except Exception as e:
            logger.error(f"Ошибка создания URL в Supabase: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка создания URL: {str(e)}"
            )
        
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
        try:
            response = db_manager.supabase.table(db_manager.url_table).select("*").eq("id", url_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"URL с ID {url_id} не найден"
                )
            
            row = response.data[0]
            url_data = {
                "id": row["id"],
                "url": row["url"],
                "title": row.get("title"),
                "description": row.get("description"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
                "is_active": row.get("is_active", True)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка получения URL из Supabase: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка получения URL: {str(e)}"
            )
        
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
        try:
            response = db_manager.supabase.table(db_manager.url_table).select("*").eq("id", url_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"URL с ID {url_id} не найден"
                )
            
            existing_url = response.data[0]
            
            # Формируем данные для обновления (убираем description - поля нет в таблице)
            update_data = {}

            if url_data.title is not None:
                update_data["title"] = url_data.title

            if url_data.is_active is not None:
                update_data["is_active"] = url_data.is_active
            
            if not update_data:
                # Если нет полей для обновления, возвращаем текущие данные
                url_data = {
                    "id": existing_url["id"],
                    "url": existing_url["url"],
                    "title": existing_url.get("title"),
                    "description": existing_url.get("description"),
                    "created_at": existing_url.get("created_at"),
                    "updated_at": existing_url.get("updated_at"),
                    "is_active": existing_url.get("is_active", True)
                }
                
                return ApiResponse(
                    status="success",
                    message="URL не был изменен",
                    data=url_data
                )
            
            # Обновляем URL
            response = db_manager.supabase.table(db_manager.url_table).update(update_data).eq("id", url_id).execute()
            
            if response.data:
                updated_url = {
                    "id": response.data[0]["id"],
                    "url": response.data[0]["url"],
                    "title": response.data[0].get("title"),
                    "description": response.data[0].get("description"),
                    "created_at": response.data[0].get("created_at"),
                    "updated_at": response.data[0].get("updated_at"),
                    "is_active": response.data[0].get("is_active", True)
                }
            else:
                raise Exception("Ошибка обновления URL")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка обновления URL в Supabase: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка обновления URL: {str(e)}"
            )
        
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
        try:
            response = db_manager.supabase.table(db_manager.url_table).select("id").eq("id", url_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"URL с ID {url_id} не найден"
                )
            
            # Удаляем связанные данные бронирования
            db_manager.supabase.table(db_manager.booking_table).delete().eq("url_id", url_id).execute()
            
            # Удаляем URL
            db_manager.supabase.table(db_manager.url_table).delete().eq("id", url_id).execute()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка удаления URL в Supabase: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка удаления URL: {str(e)}"
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
        
        # Выполняем запрос через Supabase
        try:
            response = db_manager.supabase.table(db_manager.booking_table).select("*").order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            
            booking_data = []
            total_count = len(response.data) if response.data else 0
            
            for row in response.data or []:
                data = {
                    "id": row.get("id"),
                    "url": row.get("url", ""),
                    "date": row.get("date", ""),
                    "time": row.get("time", ""),
                    "price": row.get("price", ""),
                    "provider": row.get("provider", ""),
                    "seat_number": row.get("seat_number"),
                    "location_name": row.get("location_name"),
                    "court_type": row.get("court_type"),
                    "time_category": row.get("time_category"),
                    "duration": row.get("duration"),
                    "review_count": row.get("review_count"),
                    "prepayment_required": row.get("prepayment_required"),
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("updated_at")
                }
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
            logger.error(f"Ошибка получения данных из Supabase: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при получении данных бронирования: {str(e)}"
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
        
        # Путь к файлу (используем /tmp для временных файлов)
        export_dir = "/tmp"
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, filename)
        
        # Получаем URL для запроса
        request_url = None
        if url:
            request_url = url
        elif url_id:
            try:
                response = db_manager.supabase.table(db_manager.url_table).select("url").eq("id", url_id).execute()
                if response.data:
                    request_url = response.data[0]["url"]
            except Exception as e:
                logger.error(f"Ошибка получения URL по ID: {e}")
        
        # Экспортируем данные (упрощенная версия)
        try:
            # Получаем данные через Supabase
            response = db_manager.supabase.table(db_manager.booking_table).select("*").execute()
            data = response.data or []
            
            if format.lower() == "csv":
                import csv
                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    if data:
                        fieldnames = data[0].keys()
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(data)
            else:
                import json
                with open(filepath, 'w', encoding='utf-8') as jsonfile:
                    json.dump(data, jsonfile, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            logger.error(f"Ошибка экспорта: {str(e)}")
            filepath = None
        
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
        return ApiResponse(
            status="success",
            message="Данные аналитики получены",
            data={
                "price_ranges": [],
                "price_comparison": []
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
        return ApiResponse(
            status="success",
            message="Данные доступности получены",
            data={
                "availability": [],
                "venues": []
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
        return ApiResponse(
            status="success",
            message="История цен получена",
            data={
                "price_history": []
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
        filepath = os.path.join("/tmp", filename)
        
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
            try:
                response = db_manager.supabase.table(db_manager.url_table).select("url").eq("id", url_id).execute()
                if response.data:
                    parse_url = response.data[0]["url"]
            except Exception as e:
                logger.error(f"Ошибка получения URL по ID: {e}")
        
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
        
        try:
            if active_only:
                response = db_manager.supabase.table(db_manager.url_table).select("url").eq("is_active", True).execute()
            else:
                response = db_manager.supabase.table(db_manager.url_table).select("url").execute()
            
            if response.data:
                urls = [row["url"] for row in response.data]
        except Exception as e:
            logger.error(f"Ошибка получения списка URL: {e}")
        
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
