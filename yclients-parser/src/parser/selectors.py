"""
Selectors - Константы CSS/XPath-селекторов для парсинга YCLIENTS.

Модуль содержит все селекторы, необходимые для извлечения данных с различных страниц YCLIENTS.
"""

# Селекторы для поиска элементов на странице
SELECTORS = {
    # Селекторы для обнаружения анти-бот защиты
    "captcha": ".g-recaptcha, .captcha, .cf-captcha-container",
    "ip_blocked": "#captcha-page, .cf-error-code, .cf-error-details",
    
    # Селекторы для работы с календарем и датами
    "calendar": ".booking-calendar, .calendar, .calendar-container, .date-picker",
    "available_dates": ".available-date, .date-available, .calendar-day:not(.disabled), .day-available, [data-available='true']",
    "date_selector": ".calendar-day[data-date='{date}'], .date-item[data-date='{date}'], .day[data-date='{date}']",
    
    # Селекторы для работы с временными слотами
    "time_slots_container": ".time-slots, .slots-container, .booking-time-slots, .booking-times",
    "time_slots": ".time-slot:not(.disabled), .slot:not(.disabled), .booking-time:not(.disabled), .time-item:not(.disabled)",
    "slot_price": ".slot-price, .price, .service-price, .booking-price",
    "slot_provider": ".slot-provider, .provider-name, .staff-name, .booking-provider",
    "slot_seat": ".slot-seat, .seat-number, .court-number, .room-number, .place-number",
    
    # Селекторы для информации о услугах
    "services_container": ".services-list, .services-container, .service-items",
    "service_item": ".service-item, .service, .service-option",
    "service_title": ".service-title, .service-name, .service-label",
    "service_price": ".service-price, .price-value, .price-amount",
    "service_duration": ".service-duration, .duration, .time-duration",
    
    # Селекторы для информации о сотрудниках
    "staff_container": ".staff-list, .specialists-list, .team-list",
    "staff_item": ".staff-item, .specialist-item, .team-member",
    "staff_name": ".staff-name, .specialist-name, .member-name",
    "staff_position": ".staff-position, .specialist-position, .member-position",
    "staff_avatar": ".staff-avatar, .specialist-photo, .member-photo",
    
    # Селекторы для навигации
    "next_month": ".next-month, .calendar-next, .next-btn, .btn-next",
    "prev_month": ".prev-month, .calendar-prev, .prev-btn, .btn-prev",
    "current_month": ".current-month, .calendar-month, .month-title",
    
    # Селекторы для ошибок и уведомлений
    "error_message": ".error-message, .alert-error, .notification-error",
    "success_message": ".success-message, .alert-success, .notification-success",
    
    # Селекторы для формы бронирования
    "booking_form": ".booking-form, .reservation-form, .appointment-form",
    "name_input": "#name, #client-name, input[name='name']",
    "phone_input": "#phone, #client-phone, input[name='phone']",
    "email_input": "#email, #client-email, input[name='email']",
    "comment_input": "#comment, #client-comment, textarea[name='comment']",
    "submit_button": ".submit-button, .book-button, .reserve-button, .btn-book",
    
    # Селекторы для статуса бронирования
    "booking_status": ".booking-status, .reservation-status, .appointment-status",
    "booking_confirmed": ".booking-confirmed, .reservation-confirmed, .status-confirmed",
    "booking_pending": ".booking-pending, .reservation-pending, .status-pending",
    "booking_number": ".booking-number, .reservation-number, .appointment-number",
    
    # Селекторы для поп-апов и модальных окон
    "modal_window": ".modal, .modal-window, .popup, .popup-window",
    "modal_close": ".modal-close, .close-modal, .popup-close, .close-popup",
    "modal_title": ".modal-title, .popup-title, .modal-header h4, .popup-header h4",
    "modal_content": ".modal-content, .popup-content, .modal-body, .popup-body",
    
    # Селекторы для фильтров и сортировки
    "filter_container": ".filters, .filter-options, .search-filters",
    "sort_options": ".sort-options, .sorting, .sort-controls",
    "filter_item": ".filter-item, .filter-option, .filter-control",
    "apply_filter": ".apply-filter, .submit-filter, .filter-apply",
    "clear_filter": ".clear-filter, .reset-filter, .filter-clear",
    
    # Дополнительные селекторы для специфических особенностей YCLIENTS
    "yclients_main_container": "#ycwidget, .ycwidget, #yclients-booking-widget",
    "yclients_loader": ".yclients-loader, .widget-loader, .booking-loader",
    "yclients_error": ".yclients-error, .widget-error, .booking-error"
}

# Селекторы конкретно для YCLIENTS, которые могут отличаться от общих паттернов
YCLIENTS_SPECIFIC_SELECTORS = {
    # Селекторы для работы с календарем YCLIENTS
    "yclients_calendar": ".booking-content__calendar",
    "yclients_available_dates": ".calendar__day:not(.calendar__day_disable)",
    "yclients_date_selector": ".calendar__day[data-date='{date}']",
    
    # Селекторы для работы с временными слотами YCLIENTS
    "yclients_time_slots_container": ".record__time-slots",
    "yclients_time_slots": ".record__time-slot",
    "yclients_slot_price": ".record__price",
    "yclients_slot_provider": ".record__staff",
    "yclients_slot_seat": ".record__seat, .record__place",
    
    # Селекторы для информации о услугах YCLIENTS
    "yclients_services_container": ".record__services",
    "yclients_service_item": ".record__service",
    "yclients_service_title": ".record__service-title",
    "yclients_service_price": ".record__service-price",
    "yclients_service_duration": ".record__service-duration",
    
    # Селекторы для информации о сотрудниках YCLIENTS
    "yclients_staff_container": ".record__staffs",
    "yclients_staff_item": ".record__staff",
    "yclients_staff_name": ".record__staff-name",
    "yclients_staff_position": ".record__staff-position",
    "yclients_staff_avatar": ".record__staff-avatar img",
    
    # Специфические селекторы YCLIENTS для виджета бронирования
    "yclients_widget_container": "#ycwidget",
    "yclients_widget_loader": ".ycwidget-loader",
    "yclients_widget_step_service": ".ycwidget-step__services",
    "yclients_widget_step_staff": ".ycwidget-step__staffs",
    "yclients_widget_step_date": ".ycwidget-step__dates",
    "yclients_widget_step_time": ".ycwidget-step__times",
    "yclients_widget_step_client": ".ycwidget-step__client",
    "yclients_widget_step_confirm": ".ycwidget-step__confirm"
}

# Объединяем общие селекторы и специфичные для YCLIENTS
SELECTORS.update(YCLIENTS_SPECIFIC_SELECTORS)

# Создаем дополнительные удобные группировки селекторов по функциональности
# Эти группировки могут быть использованы для более структурированного доступа
CALENDAR_SELECTORS = {k: v for k, v in SELECTORS.items() if any(
    x in k for x in ['calendar', 'date', 'month', 'day']
)}

TIME_SELECTORS = {k: v for k, v in SELECTORS.items() if any(
    x in k for x in ['time', 'slot', 'duration']
)}

STAFF_SELECTORS = {k: v for k, v in SELECTORS.items() if any(
    x in k for x in ['staff', 'provider', 'specialist']
)}

SERVICE_SELECTORS = {k: v for k, v in SELECTORS.items() if any(
    x in k for x in ['service']
)}

BOOKING_FORM_SELECTORS = {k: v for k, v in SELECTORS.items() if any(
    x in k for x in ['form', 'input', 'button', 'submit']
)}

YCLIENTS_SELECTORS = {k: v for k, v in SELECTORS.items() if 'yclients' in k}

# XPath селекторы, которые могут быть полезны в случае сложных структур
XPATH_SELECTORS = {
    # XPath селекторы для обхода сложных структур
    "all_visible_dates": "//div[contains(@class, 'calendar') or contains(@class, 'dates')]//div[not(contains(@class, 'disabled')) and not(contains(@class, 'hidden'))]",
    "all_visible_times": "//div[contains(@class, 'time') or contains(@class, 'slot')]//div[not(contains(@class, 'disabled')) and not(contains(@class, 'hidden'))]",
    "all_staff_names": "//div[contains(@class, 'staff') or contains(@class, 'provider')]//span[contains(@class, 'name')]",
    "all_service_names": "//div[contains(@class, 'service')]//span[contains(@class, 'name') or contains(@class, 'title')]",
    
    # XPath селекторы для извлечения текстовых данных с атрибутами
    "date_with_attribute": "//div[@data-date]",
    "time_with_attribute": "//div[@data-time]",
    "price_with_text": "//div[contains(@class, 'price')]/text()",
    "seat_with_text": "//div[contains(@class, 'seat') or contains(@class, 'place')]/text()",
    
    # Специфичные XPath селекторы для YCLIENTS
    "yclients_calendar_days": "//div[contains(@class, 'calendar__day')]",
    "yclients_time_slots": "//div[contains(@class, 'record__time-slot')]"
}

# Рекурсивные селекторы для сложных вложенных структур
RECURSIVE_SELECTORS = {
    "nested_services": ".service-item .service-subitem, .service-option .service-suboption",
    "nested_staff": ".staff-item .staff-subitem, .team-member .team-submember",
    "nested_dates": ".calendar-month .calendar-week .calendar-day"
}

# Экспортируем все группы селекторов для удобства использования
__all__ = [
    'SELECTORS',
    'YCLIENTS_SPECIFIC_SELECTORS',
    'CALENDAR_SELECTORS',
    'TIME_SELECTORS',
    'STAFF_SELECTORS',
    'SERVICE_SELECTORS',
    'BOOKING_FORM_SELECTORS',
    'YCLIENTS_SELECTORS',
    'XPATH_SELECTORS',
    'RECURSIVE_SELECTORS'
]
