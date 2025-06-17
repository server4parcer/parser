# Обновленные селекторы для реального сайта YClients
# Основываются на анализе реальной структуры HTML

# Селекторы для реального YClients сайта
REAL_YCLIENTS_SELECTORS = {
    # Селекторы для цены - ИЗБЕГАЕМ элементы со временем!
    "price_selectors": [
        # Наиболее вероятные селекторы для цены на YClients
        "[data-price]",                    # Элемент с атрибутом data-price
        ".service-price",                  # Класс service-price
        ".booking-price",                  # Класс booking-price  
        ".price-value",                    # Класс price-value
        ".cost",                          # Класс cost
        ".amount",                        # Класс amount
        ".fee",                           # Класс fee
        ".tariff",                        # Класс tariff
        
        # Более специфичные для YClients
        ".record-service-price",          # YClients специфичный
        ".yclients-price",               # YClients специфичный
        ".slot-price-info",              # Слот с информацией о цене
        ".booking-cost-info",            # Информация о стоимости
        
        # Через текст (последний приоритет)
        "*[title*='цена']",              # Элемент с title содержащим "цена"
        "*[title*='стоимость']",         # Элемент с title содержащим "стоимость"
        "*[title*='price']",             # Элемент с title содержащим "price"
    ],
    
    # Селекторы для провайдера/сотрудника
    "provider_selectors": [
        # Наиболее вероятные селекторы для имени сотрудника
        "[data-staff]",                   # Элемент с атрибутом data-staff
        "[data-staff-name]",             # Элемент с атрибутом data-staff-name
        "[data-specialist]",             # Элемент с атрибутом data-specialist
        "[data-master]",                 # Элемент с атрибутом data-master
        "[data-employee]",               # Элемент с атрибутом data-employee
        
        ".staff-name",                   # Класс staff-name
        ".specialist-name",              # Класс specialist-name
        ".master-name",                  # Класс master-name
        ".employee-name",                # Класс employee-name
        ".provider-name",                # Класс provider-name
        ".worker-name",                  # Класс worker-name
        
        # Более специфичные для YClients
        ".record-staff-name",            # YClients специфичный
        ".yclients-staff",              # YClients специфичный
        ".booking-specialist",           # Специалист бронирования
        ".service-provider",             # Провайдер услуги
        
        # Через текст и title
        "*[title*='специалист']",        # Элемент с title содержащим "специалист"
        "*[title*='мастер']",           # Элемент с title содержащим "мастер"
        "*[title*='сотрудник']",        # Элемент с title содержащим "сотрудник"
    ],
    
    # Селекторы для времени (чтобы НЕ путать с ценой)
    "time_selectors": [
        "[data-time]",                   # Элемент с атрибутом data-time
        ".time",                         # Класс time
        ".slot-time",                    # Класс slot-time
        ".booking-time",                 # Класс booking-time
        ".schedule-time",                # Класс schedule-time
        ".appointment-time",             # Класс appointment-time
    ],
    
    # Селекторы для временных слотов
    "time_slot_selectors": [
        ".time-slot",                    # Класс time-slot
        ".booking-slot",                 # Класс booking-slot
        ".schedule-slot",                # Класс schedule-slot
        ".appointment-slot",             # Класс appointment-slot
        ".available-slot",               # Класс available-slot
        "[data-slot]",                   # Элемент с атрибутом data-slot
    ],
    
    # Селекторы для дат
    "date_selectors": [
        "[data-date]",                   # Элемент с атрибутом data-date
        ".date",                         # Класс date
        ".calendar-date",                # Класс calendar-date
        ".booking-date",                 # Класс booking-date
    ],
    
    # Исключения - элементы которые НЕ должны содержать цену
    "price_exclude_selectors": [
        ".time",                         # Исключаем элементы времени
        ".clock",                        # Исключаем часы
        ".duration",                     # Исключаем продолжительность
        "[data-time]",                   # Исключаем элементы с data-time
        ".slot-time",                    # Исключаем время слотов
    ]
}

# Паттерны для определения валидности данных
VALIDATION_PATTERNS = {
    # Паттерны для цены (должны содержать валюту или явно цену)
    "price_patterns": [
        r'\d+\s*(?:₽|руб|рублей?|р\.?)\s*',                    # Рубли
        r'\d+\s*(?:\$|USD|долларов?)\s*',                      # Доллары  
        r'\d+\s*(?:€|EUR|евро)\s*',                           # Евро
        r'(?:₽|руб|рублей?|р\.?)\s*\d+',                      # Валюта перед числом
        r'(?:\$|USD|долларов?)\s*\d+',                        # Доллары перед числом
        r'(?:€|EUR|евро)\s*\d+',                              # Евро перед числом
        r'(?:цена|стоимость|price|cost)[:=]\s*\d+',           # "цена: 1500"
        r'\d+\s*(?:тенге|тг)',                                # Тенге
    ],
    
    # Паттерны для времени (исключаем из цены)
    "time_patterns": [
        r'\b([01]?\d|2[0-3]):([0-5]\d)\b',                    # HH:MM формат
        r'\b([01]?\d|2[0-3])\s*ч\s*([0-5]\d)?\s*м?\b',       # "14ч 30м" формат
        r'\b(1[0-2]|0?[1-9])\s*(AM|PM)\b',                    # 12-часовой формат
    ],
    
    # Паттерны для имен (валидные имена)
    "name_patterns": [
        r'\b[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)*\b',           # Русские имена
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',               # Английские имена
        r'\b[А-ЯЁA-Z][а-яёa-z]+(?:\s+[А-ЯЁA-Z]\.?\s*)*[А-ЯЁA-Z][а-яёa-z]+\b', # Имя с инициалами
    ],
    
    # Исключения для имен (не должны быть именами)
    "name_exclude_patterns": [
        r'^\d+$',                                             # Только цифры
        r'\d+\s*(?:₽|руб|рублей?|р\.?|\$|€)',                # Цены
        r'\b([01]?\d|2[0-3]):([0-5]\d)\b',                   # Время
        r'^(не\s+указан|не\s+выбран|нет\s+данных)$',         # Пустые значения
    ]
}

async def find_best_selector_for_element(page, selector_list, element_description="элемент"):
    """
    Находит лучший селектор из списка для текущей страницы.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    for selector in selector_list:
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                # Дополнительно проверяем содержимое элементов
                for element in elements[:3]:  # Проверяем первые 3 элемента
                    text = await element.text_content()
                    if text and text.strip():
                        logger.info(f"✅ Рабочий селектор для {element_description}: {selector} (найдено {len(elements)} элементов)")
                        return selector
        except Exception as e:
            logger.debug(f"🔍 Селектор {selector} не работает: {str(e)}")
    
    logger.warning(f"⚠️ Не найдено рабочих селекторов для {element_description}")
    return None

def is_valid_price(text):
    """Проверяет, является ли текст валидной ценой."""
    import re
    
    if not text:
        return False
    
    text = text.strip()
    
    # Проверяем что это не время
    for pattern in VALIDATION_PATTERNS["time_patterns"]:
        if re.search(pattern, text):
            return False
    
    # Проверяем что это похоже на цену
    for pattern in VALIDATION_PATTERNS["price_patterns"]:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Проверяем простое число с возможной валютой
    if re.search(r'\d+', text):
        return True
    
    return False

def is_valid_name(text):
    """Проверяет, является ли текст валидным именем."""
    import re
    
    if not text:
        return False
    
    text = text.strip()
    
    # Исключаем явно невалидные имена
    for pattern in VALIDATION_PATTERNS["name_exclude_patterns"]:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    
    # Проверяем на валидные паттерны имен
    for pattern in VALIDATION_PATTERNS["name_patterns"]:
        if re.search(pattern, text):
            return True
    
    # Минимальная проверка - есть буквы и длина больше 2
    if len(text) >= 2 and re.search(r'[А-Яа-яA-Za-z]', text):
        return True
    
    return False
