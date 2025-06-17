"""
Updated YClients Selectors - based on real YClients website structure.
These selectors are specifically designed to avoid the time/price confusion bug.
"""

# Updated selectors for the real YClients website structure
YCLIENTS_REAL_SELECTORS = {
    # Service selection page elements
    "service_page": {
        "services_container": ".services-list, .record-services, .booking-services",
        "service_items": ".service-item, .record-service, .booking-service",
        "service_links": "a[href*='record'], .service-link, .booking-link",
        "service_names": ".service-name, .service-title, .record-service-name"
    },
    
    # Calendar and date selection
    "calendar": {
        "calendar_container": ".calendar, .datepicker, .booking-calendar, .rc-calendar",
        "available_dates": ".available-date, .selectable-date, .calendar-day:not(.disabled)",
        "date_buttons": "[data-date], .calendar-date, .date-option",
        "date_selector": "[data-date='{date}'], .calendar-day[data-value='{date}']"
    },
    
    # Time slots - CAREFULLY SEPARATED FROM PRICE
    "time_slots": {
        "container": ".time-slots, .time-list, .schedule-list, .available-times",
        "slots": ".time-slot, .schedule-item, .time-option, .booking-slot",
        
        # TIME elements (to extract time, NOT confuse with price)
        "time_elements": [
            ".slot-time:not(.price)",      # Time element that's NOT price
            ".time-value:not(.cost)",      # Time value that's NOT cost
            ".schedule-time:not(.amount)", # Schedule time that's NOT amount
            "[data-time]:not([data-price])", # Has data-time but NOT data-price
            ".time:not(.price-time)",      # Time class but NOT price-time
            ".booking-time:not(.booking-price)"  # Booking time but NOT booking price
        ],
        
        # PRICE elements (explicitly for prices, avoid time elements)
        "price_elements": [
            ".slot-price:not(.time)",          # Price element that's NOT time
            ".service-price:not(.duration)",   # Service price that's NOT duration
            ".booking-cost:not(.time-cost)",   # Booking cost that's NOT time-cost
            "[data-price]:not([data-time])",   # Has data-price but NOT data-time
            ".price:not(.time-price)",         # Price class but NOT time-price
            ".cost:not(.time):not(.duration)", # Cost that's NOT time or duration
            ".amount:not(.time-amount)",       # Amount that's NOT time-amount
            ".tariff, .fee, .rubles"           # Other price indicators
        ],
        
        # PROVIDER/STAFF elements
        "provider_elements": [
            ".staff-name, .specialist-name, .master-name",
            ".provider-name, .employee-name, .worker-name",
            "[data-staff], [data-specialist], [data-master]",
            "[data-staff-name], [data-provider-name]",
            ".booking-staff, .service-provider"
        ]
    },
    
    # Anti-patterns - elements to AVOID when looking for prices
    "avoid_for_price": [
        ".time", ".clock", ".duration", ".schedule",
        "[data-time]", ".time-value", ".time-display",
        ".hour", ".minute", ".am-pm",
        ".slot-time", ".booking-time", ".schedule-time"
    ],
    
    # Loading and error states
    "states": {
        "loading": ".loading, .spinner, .loader, .preloader",
        "error": ".error, .alert, .message-error, .booking-error",
        "empty": ".empty, .no-data, .no-slots, .no-availability"
    }
}

# CSS selector combinations that work well for YClients
YCLIENTS_COMBINED_SELECTORS = {
    # Find slots that have both time and price info
    "complete_slots": [
        ".time-slot:has(.time):has(.price)",
        ".booking-slot:has([data-time]):has([data-price])", 
        ".schedule-item:has(.slot-time):has(.slot-price)"
    ],
    
    # Find prices that are definitely not time-related
    "safe_prices": [
        ".price:not(.time):not([data-time]):not(.duration)",
        "[data-price]:not(.time):not([data-time]):not(.schedule)",
        ".cost:not(.time-cost):not(.duration):not(.schedule-cost)",
        ".amount:not(.time):not(.duration):not(.schedule)"
    ],
    
    # Find provider info that's not confused with other data
    "safe_providers": [
        ".staff:not(.time):not(.price):not(.cost)",
        "[data-staff]:not([data-time]):not([data-price])",
        ".specialist:not(.duration):not(.amount)"
    ]
}

# XPath selectors for complex scenarios
YCLIENTS_XPATH_SELECTORS = {
    # Get price text that doesn't contain time patterns
    "price_no_time": [
        "//span[contains(@class, 'price') and not(contains(text(), ':')) and not(contains(@class, 'time'))]/text()",
        "//div[contains(@class, 'cost') and not(contains(text(), ':')) and not(contains(@class, 'duration'))]/text()",
        "//span[contains(text(), '₽') and not(contains(text(), ':'))]/text()",
        "//span[contains(text(), 'руб') and not(contains(text(), ':'))]/text()"
    ],
    
    # Get time that's not confused with price
    "time_no_price": [
        "//span[contains(@class, 'time') and not(contains(@class, 'price')) and contains(text(), ':')]/text()",
        "//div[@data-time and not(@data-price)]/text()",
        "//span[contains(text(), ':') and not(contains(text(), '₽')) and not(contains(text(), 'руб'))]/text()"
    ],
    
    # Get provider names
    "provider_names": [
        "//span[contains(@class, 'staff') or contains(@class, 'specialist')]/text()",
        "//div[@data-staff-name]/text()",
        "//span[contains(@class, 'master') and not(contains(@class, 'time'))]/text()"
    ]
}

# Validation patterns specifically for YClients data
YCLIENTS_VALIDATION = {
    # Price patterns that are valid for YClients
    "valid_price_patterns": [
        r'^\d{3,5}\s*₽$',           # 100₽, 1500₽, 10000₽ (minimum 3 digits)
        r'^\d{3,5}\s*руб\.?$',      # 100руб, 1500руб. (minimum 3 digits)
        r'^\d{3,5}\s*рублей?$',     # 100 рублей (minimum 3 digits)
        r'^от\s+\d{2,5}\s*₽$',      # от 50₽, от 1500₽
        r'^\d{3,5}-\d{3,5}\s*₽$',   # 100-2000₽ (price range, minimum 3 digits)
        r'^[24-9]\d\s*₽$',          # 24₽ to 99₽ (excludes 0-23)
        r'^[1-9]\d{2,}\s*₽$'        # 100₽+ (3+ digits)
    ],
    
    # Time patterns to exclude from prices
    "time_patterns_to_exclude": [
        r'^\d{1,2}:\d{2}$',         # 22:00, 7:30
        r'^\d{1,2}:\d{2}:\d{2}$',   # 22:00:00
        r'^\d{1,2}\s*ч\s*\d{0,2}\s*м?$'  # 2ч 30м, 1ч
    ],
    
    # Provider name patterns for Russian names
    "valid_provider_patterns": [
        r'^[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.$',           # Имя И.
        r'^[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+$',       # Имя Фамилия  
        r'^[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.$', # Фамилия И.О.
        r'^[А-ЯЁ][а-яё]{2,}$'                     # Одно имя
    ]
}

def get_safe_price_selector():
    """Returns the safest CSS selector for finding prices."""
    return ", ".join(YCLIENTS_COMBINED_SELECTORS["safe_prices"])

def get_safe_time_selector():
    """Returns the safest CSS selector for finding time."""
    return ", ".join(YCLIENTS_REAL_SELECTORS["time_slots"]["time_elements"])

def get_safe_provider_selector():
    """Returns the safest CSS selector for finding providers."""
    return ", ".join(YCLIENTS_COMBINED_SELECTORS["safe_providers"])

def is_valid_yclients_price(text: str) -> bool:
    """Check if text matches YClients price patterns."""
    import re
    if not text:
        return False
    
    text = text.strip()
    
    # First check it's not time
    for pattern in YCLIENTS_VALIDATION["time_patterns_to_exclude"]:
        if re.match(pattern, text):
            return False
    
    # CRITICAL: Check if it's a suspicious hour value with currency
    # Extract number from price text
    price_number_match = re.search(r'(\d+)', text)
    if price_number_match:
        number = int(price_number_match.group(1))
        # If it's 0-23, it's likely an hour that got currency added
        if 0 <= number <= 23:
            return False
    
    # Then check it matches price patterns
    for pattern in YCLIENTS_VALIDATION["valid_price_patterns"]:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    return False

def is_valid_yclients_provider(text: str) -> bool:
    """Check if text matches YClients provider name patterns."""
    import re
    if not text or len(text.strip()) < 2:
        return False
    
    text = text.strip()
    
    # Exclude obviously invalid names
    if text.lower() in ['не указан', 'нет', 'none', 'null', '']:
        return False
    
    # Check against provider patterns
    for pattern in YCLIENTS_VALIDATION["valid_provider_patterns"]:
        if re.match(pattern, text):
            return True
    
    # Basic fallback - contains letters and no numbers/symbols
    if re.match(r'^[А-ЯЁа-яёA-Za-z\s\.\-]+$', text) and not re.search(r'\d', text):
        return True
    
    return False

# Export the main selectors
SELECTORS = YCLIENTS_REAL_SELECTORS

__all__ = [
    'YCLIENTS_REAL_SELECTORS',
    'YCLIENTS_COMBINED_SELECTORS', 
    'YCLIENTS_XPATH_SELECTORS',
    'YCLIENTS_VALIDATION',
    'SELECTORS',
    'get_safe_price_selector',
    'get_safe_time_selector', 
    'get_safe_provider_selector',
    'is_valid_yclients_price',
    'is_valid_yclients_provider'
]
