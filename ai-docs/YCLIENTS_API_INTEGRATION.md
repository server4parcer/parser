# YClients API Integration Guide

**AI Agent Memory Document**  
*Third-party API documentation and integration details for YClients parser*

## 🎯 YClients Platform Overview

### **What is YClients**
- Russian online booking platform for sports venues, salons, and services
- Provides booking widgets embedded in business websites
- Uses dynamic JavaScript loading for time slots and availability
- Implements anti-bot protection and rate limiting

### **URL Patterns**
```
Service Selection: https://yclients.com/company/{id}/record-type?o=
Direct Booking:    https://yclients.com/company/{id}/booking
Company Profile:   https://yclients.com/company/{id}
```

## 🏗️ YClients DOM Structure

### **Service Selection Page**
```css
.service-item           /* Individual service options */
.service-option         /* Alternative service selector */
.record__service        /* Service in record flow */
.ycwidget-service       /* Widget-embedded services */
.booking-service-item   /* Booking flow services */
```

### **Calendar & Date Selection**
```css
.calendar-container     /* Main calendar wrapper */
.available-dates        /* Available date elements */
[data-date]            /* Date with data attribute */
.date-selector         /* Individual date selectors */
```

### **Time Slots**
```css
.time-slot             /* Individual time slot */
.slot-time             /* Time display element */
.slot-price            /* Price display element */
.slot-available        /* Available slot indicator */
.booking-slot          /* Alternative slot selector */
```

### **Price Elements** (CRITICAL - avoid time confusion)
```css
/* SAFE price selectors */
.slot-price:not(.time)
.service-price:not(.duration)
.booking-cost:not(.time-cost)
[data-price]:not([data-time])
.price:not(.time-price)

/* AVOID these (likely time elements) */
.time, .clock, .duration, .schedule
[data-time], .time-value, .time-display
.hour, .minute, .am-pm
```

### **Provider/Staff Elements**
```css
.staff-name            /* Staff member name */
.specialist            /* Service specialist */
.master                /* Alternative staff title */
[data-staff-name]      /* Staff data attribute */
.provider              /* Service provider */
```

## 🔒 Anti-Bot Protection

### **Detection Methods**
- CAPTCHA/reCAPTCHA on suspicious activity
- User-Agent validation
- JavaScript execution requirements
- Rate limiting per IP
- Session fingerprinting

### **Mitigation Strategies**
```python
# Browser stealth configuration
BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-site-isolation-trials",
    "--disable-web-security"
]

# Random delays between requests
await asyncio.sleep(random.uniform(1, 3))

# User-Agent rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/96.0.4664.110",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36"
]
```

## 📡 HTTP Request Patterns

### **Initial Page Load**
```http
GET /company/{id}/booking HTTP/1.1
Host: yclients.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/96.0.4664.110
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3
```

### **AJAX Requests for Time Slots**
```http
POST /api/booking/available-times HTTP/1.1
Host: yclients.com
Content-Type: application/json
X-Requested-With: XMLHttpRequest

{
  "service_id": 12345,
  "date": "2025-08-05",
  "location_id": 678
}
```

### **Common Response Format**
```json
{
  "status": "success",
  "data": {
    "available_times": [
      {
        "time": "10:00",
        "price": 2500,
        "staff_id": 123,
        "staff_name": "Анна Иванова",
        "duration": 60,
        "available": true
      }
    ]
  }
}
```

## 🔄 Data Flow Patterns

### **Navigation Sequence**
1. **Load service selection page** → Parse available services
2. **Select service** → Get booking page for specific service
3. **Load calendar** → Extract available dates
4. **Select date** → Get available time slots
5. **Extract slot data** → Parse time, price, staff, duration

### **Dynamic Loading**
- Time slots loaded via AJAX after date selection
- Prices may change based on time of day/week
- Availability updates in real-time
- Some data requires JavaScript execution

## 🎨 Data Extraction Patterns

### **Time Format Validation**
```python
# Valid time patterns
TIME_PATTERNS = [
    r'^\d{1,2}:\d{2}$',      # 10:00, 9:30
    r'^\d{1,2}:\d{2}:\d{2}$'  # 10:00:00
]

# Invalid time-as-price patterns (AVOID)
INVALID_PRICE_PATTERNS = [
    r'^\d{1,2}:\d{2}$',      # Time mistaken as price
    r'^[0-2]?\d$',           # Hour numbers (0-23)
    r'^\d{1,2}₽$'            # Hour with currency
]
```

### **Business Analytics Enhancement**
```python
# Court type detection
COURT_TYPES = {
    'tennis': ['теннис', 'корт', 'tennis'],
    'basketball': ['баскетбол', 'basketball'],
    'squash': ['сквош', 'squash'],
    'general': ['зал', 'площадка', 'hall']
}

# Time categorization
def categorize_time(hour, is_weekend):
    if is_weekend:
        return "WEEKEND"
    elif hour < 17:
        return "DAY"
    else:
        return "EVENING"
```

## 🚫 Common Pitfalls

### **Price vs Time Confusion** ⚠️
- YClients often displays time in price-like formats
- "10₽" might actually be "10:00" (10 AM)
- Always validate that price contains currency symbols
- Cross-check with time field to avoid duplicates

### **Dynamic Content Loading**
- Initial page may not contain time slots
- Requires waiting for JavaScript execution
- Network timeout handling essential
- Retry logic for failed AJAX requests

### **Rate Limiting**
- Too many requests trigger blocking
- Implement delays between requests (2-5 seconds)
- Rotate IP addresses/proxies
- Monitor for CAPTCHA appearance

## 🔧 Integration Best Practices

### **Robust Error Handling**
```python
try:
    # YClients request
    response = await session.get(url, timeout=30)
    if response.status == 429:  # Rate limited
        await asyncio.sleep(60)  # Wait 1 minute
        continue
    elif response.status >= 400:
        logger.error(f"HTTP {response.status}: {url}")
        return []
except asyncio.TimeoutError:
    logger.error(f"Timeout: {url}")
    return []
```

### **Data Validation Pipeline**
1. **Raw Extraction** → Get all text content
2. **Format Validation** → Check time/price patterns
3. **Business Logic** → Apply court type detection
4. **Cross-Validation** → Ensure data consistency
5. **Storage** → Save to database with metadata

---

*This document contains YClients platform specifics for AI agents working on the parser system*