# Обновленные селекторы специально для YClients с исправлениями проблем
IMPROVED_YCLIENTS_SELECTORS = {
    # Более точные селекторы для цены YClients
    "price_selectors": [
        ".record__service-price",
        ".ycwidget-price", 
        ".booking-price-value",
        ".service-price-amount",
        ".slot-price-text",
        "[data-price]",
        ".price-value",
        ".cost-amount",
        ".fee-value"
    ],
    
    # Более точные селекторы для провайдера/сотрудника YClients
    "provider_selectors": [
        ".record__staff-name",
        ".ycwidget-staff-name",
        ".staff-member-name", 
        ".specialist-name-text",
        ".provider-name-text",
        ".master-name",
        ".employee-name",
        "[data-staff-name]",
        "[data-provider-name]",
        ".booking-provider-name"
    ],
    
    # Селекторы для временных слотов
    "time_slot_selectors": [
        ".record__time-item",
        ".ycwidget-time-slot",
        ".booking-time-option:not(.disabled)",
        ".time-slot-available",
        ".slot-time-value"
    ],
    
    # Селекторы для страниц выбора услуг
    "service_selection_selectors": [
        ".service-list-item",
        ".record__service-option", 
        ".ycwidget-service-item",
        ".booking-service-choice",
        ".service-category-item"
    ],
    
    # Селекторы для ссылок на услуги
    "service_link_selectors": [
        ".service-list-item a",
        ".record__service-option a",
        ".ycwidget-service-item a",
        ".booking-service-choice a",
        "[data-service-url]"
    ],
    
    # Селекторы для загрузки
    "loading_selectors": [
        ".ycwidget-loader",
        ".booking-loader", 
        ".record__loading",
        ".spinner",
        ".loading-indicator"
    ],
    
    # Селекторы для ошибок
    "error_selectors": [
        ".ycwidget-error",
        ".booking-error",
        ".record__error",
        ".error-message",
        ".alert-error"
    ]
}

# Функция для динамической проверки селекторов
async def find_best_selector(page, selector_list, element_type="element"):
    """
    Находит лучший селектор из списка для текущей страницы.
    
    Args:
        page: Playwright page object
        selector_list: Список CSS-селекторов для проверки
        element_type: Тип элемента для логирования
    
    Returns:
        str: Лучший найденный селектор или None
    """
    import logging
    logger = logging.getLogger(__name__)
    
    for selector in selector_list:
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                logger.info(f"Найден рабочий селектор для {element_type}: {selector} ({len(elements)} элементов)")
                return selector
        except Exception as e:
            logger.debug(f"Селектор {selector} не работает: {str(e)}")
    
    logger.warning(f"Не найдено рабочих селекторов для {element_type}")
    return None

# Функция для адаптивного извлечения данных
async def extract_with_adaptive_selectors(page, selector_type):
    """
    Извлекает данные используя адаптивный выбор селекторов.
    
    Args:
        page: Playwright page object
        selector_type: Тип селекторов из IMPROVED_YCLIENTS_SELECTORS
    
    Returns:
        list: Список найденных элементов
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if selector_type not in IMPROVED_YCLIENTS_SELECTORS:
        logger.error(f"Неизвестный тип селектора: {selector_type}")
        return []
    
    selectors = IMPROVED_YCLIENTS_SELECTORS[selector_type]
    best_selector = await find_best_selector(page, selectors, selector_type)
    
    if best_selector:
        elements = await page.query_selector_all(best_selector)
        logger.info(f"Извлечено {len(elements)} элементов для {selector_type}")
        return elements
    
    return []
