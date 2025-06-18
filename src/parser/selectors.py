"""
Обновленные селекторы для реального сайта YClients.
Исправляет проблему парсинга времени вместо цены.
"""

# Основные селекторы для YClients
YCLIENTS_SELECTORS = {
    # Календарь и даты
    "calendar": ".booking-calendar, .rc-calendar, .calendar",
    "available_dates": ".rc-calendar-date:not(.rc-calendar-disabled-date), .available-day, .selectable-date",
    "date_selector": ".rc-calendar-date[title*='{date}'], .calendar-day[data-date='{date}']",
    
    # Временные слоты - ОБНОВЛЕНО для предотвращения парсинга времени как цены
    "time_slots_container": ".time-slots, .slots-container, .time-list, .booking-times",
    "time_slots": ".time-slot, .slot-item, .time-item, .booking-time-slot",
    
    # Время - четко разделено от цены
    "slot_time": ".time, .slot-time, .booking-time, [data-time]",
    "time_text": ".time-text, .slot-time-value, .time-display",
    
    # Цена - ИСПРАВЛЕНО: избегаем селекторов времени
    "slot_price": [
        ".price:not(.time):not([data-time])", 
        ".cost", 
        ".amount", 
        ".service-price",
        ".booking-price", 
        ".price-value",
        ".rubles", 
        ".currency",
        "[data-price]:not([data-time])",
        ".price-amount",
        ".fee"
    ],
    
    # Провайдер/сотрудник - РАСШИРЕНО
    "slot_provider": [
        ".staff-name",
        ".provider-name", 
        ".specialist-name",
        ".master-name",
        ".employee-name",
        ".worker-name",
        ".service-provider",
        ".booking-staff",
        "[data-staff-name]",
        "[data-provider]",
        ".staff-info .name",
        ".provider-info .name",
        ".specialist",
        ".master"
    ],
    
    # Дополнительная информация
    "slot_duration": ".duration, .time-duration, .service-duration",
    "slot_description": ".description, .service-description, .booking-description",
    
    # Услуги
    "services_list": ".services-list, .service-items, .booking-services",
    "service_item": ".service-item, .service-option, .booking-service",
    "service_link": ".service-item a, .service-option a, .service-link",
    
    # Загрузка и ошибки
    "loading": ".loading, .spinner, .loader",
    "error": ".error, .alert-error, .booking-error"
}

# Специальные XPath селекторы для сложных случаев
XPATH_SELECTORS = {
    # Цена через XPath - избегаем время
    "price_xpath": [
        "//span[contains(@class, 'price') and not(contains(@class, 'time'))]/text()",
        "//div[contains(@class, 'cost') and not(contains(@class, 'time'))]/text()",
        "//span[contains(text(), '₽') or contains(text(), 'руб')]/text()",
        "//div[contains(text(), '₽') or contains(text(), 'руб')]/text()"
    ],
    
    # Провайдер через XPath
    "provider_xpath": [
        "//span[contains(@class, 'staff') or contains(@class, 'specialist')]/text()",
        "//div[contains(@class, 'provider') or contains(@class, 'master')]/text()",
        "//span[@data-staff-name]/text()",
        "//div[@data-provider]/text()"
    ],
    
    # Время через XPath
    "time_xpath": [
        "//span[contains(@class, 'time') and not(contains(@class, 'price'))]/text()",
        "//div[contains(@class, 'time') and not(contains(@class, 'cost'))]/text()",
        "//span[@data-time]/text()"
    ]
}

# Регулярные выражения для очистки данных
PATTERNS = {
    # Паттерн для времени - должен НЕ содержать валюту
    "time": r"^(\d{1,2}):(\d{2})(?:\s*(AM|PM))?$",
    
    # Паттерн для цены - должен содержать валюту или быть числом в контексте цены
    "price": r"(\d+(?:[.,]\d+)?)\s*([₽$€]|руб\.?|рублей?|долларов?|USD|EUR|RUB)",
    "price_number": r"^\d+(?:[.,]\d+)?$",
    
    # Паттерн для имен - буквы, но не числа
    "name": r"^[А-ЯЁа-яёA-Za-z\s\-\.]+$",
    
    # Исключения - что НЕ должно быть именем
    "not_name": r"^\d+$|^\d+[.,]\d+$|\d+:\d+|[₽$€]"
}

# Функции для валидации данных
def is_time_not_price(text: str) -> bool:
    """Проверяет, что текст - это время, а не цена."""
    import re
    if not text:
        return False
    
    text = text.strip()
    
    # Если содержит валюту - это точно цена
    if re.search(r"[₽$€]|руб|USD|EUR", text, re.IGNORECASE):
        return False
    
    # Если формат времени - это время
    time_pattern = re.compile(PATTERNS["time"])
    return bool(time_pattern.match(text))

def is_price_not_time(text: str) -> bool:
    """Проверяет, что текст - это цена, а не время."""
    import re
    if not text:
        return False
    
    text = text.strip()
    
    # Если содержит валюту - это цена
    if re.search(r"[₽$€]|руб|USD|EUR", text, re.IGNORECASE):
        return True
    
    # Если формат времени - это НЕ цена
    if re.match(PATTERNS["time"], text):
        return False
    
    # Если просто число без двоеточия - может быть ценой
    if re.match(PATTERNS["price_number"], text):
        return True
    
    return False

def is_valid_provider_name(text: str) -> bool:
    """Проверяет, что текст - это валидное имя провайдера."""
    import re
    if not text or len(text.strip()) < 2:
        return False
    
    text = text.strip()
    
    # Исключаем числа, время, цены
    if re.search(PATTERNS["not_name"], text):
        return False
    
    # Проверяем на валидное имя
    return bool(re.match(PATTERNS["name"], text))

# Экспорт всех селекторов
SELECTORS = YCLIENTS_SELECTORS

__all__ = [
    'SELECTORS', 
    'YCLIENTS_SELECTORS', 
    'XPATH_SELECTORS', 
    'PATTERNS',
    'is_time_not_price',
    'is_price_not_time', 
    'is_valid_provider_name'
]
