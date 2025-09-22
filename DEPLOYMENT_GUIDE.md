# YClients Parser - Production Deployment Guide

**Complete deployment instructions for the YClients parser with 4-step Playwright navigation**

---

## 🎯 **What Was Implemented**

### ✅ **Core Features**
- **4-step YClients navigation**: Service → Court → Date/Time → Prices
- **Real selector usage**: ui-kit-simple-cell, ui-kit-headline, ui-kit-title
- **Parser routing**: YClients URLs → Playwright, Others → Lightweight
- **Demo data elimination**: Zero fallback to fake data
- **Background scheduling**: Automatic parsing every 10 minutes
- **Database integration**: Supabase with real venue data

### ✅ **Implementation Summary**
- Updated `src/parser/yclients_parser.py` with `navigate_yclients_flow()` method
- Created `src/parser/parser_router.py` for intelligent URL routing
- Modified `lightweight_parser.py` to use new routing system
- Added comprehensive test suite (15 unit tests, 7 regression tests)
- All tests pass 100%

---

## 📋 **Prerequisites**

### **System Requirements**
- Python 3.11+
- Playwright browser automation
- Supabase database access

### **Install Dependencies**
```bash
# Install Python dependencies
pip install playwright requests beautifulsoup4 fastapi uvicorn supabase

# Install Playwright browsers
playwright install chromium

# Verify installation
python -c "from src.parser.parser_router import ParserRouter; print('✅ Installation successful')"
```

---

## 🔧 **Environment Configuration**

### **Required Environment Variables**
```bash
# Core Settings
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=your_secure_api_key

# Pavel's Venue URLs (Real Production URLs)
PARSE_URLS=https://n1165596.yclients.com/company/1109937/record-type?o=,https://n1308467.yclients.com/company/1192304/record-type?o=,https://b861100.yclients.com/company/804153/personal/select-time?o=m-1,https://b1009933.yclients.com/company/936902/personal/select-time?o=,https://b918666.yclients.com/company/855029/personal/menu?o=m-1

# Supabase Integration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Parsing Settings
PARSE_INTERVAL=600  # 10 minutes in seconds
```

### **Create .env File**
```bash
# Create environment file
cat > .env << 'EOF'
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=your_production_api_key

PARSE_URLS=https://n1165596.yclients.com/company/1109937/record-type?o=,https://n1308467.yclients.com/company/1192304/record-type?o=

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

PARSE_INTERVAL=600
EOF

# Load environment variables
source .env
```

---

## 🚀 **Deployment Steps**

### **Step 1: Pre-Flight Testing**
```bash
# Test imports and basic functionality
python -c "
from src.parser.parser_router import ParserRouter
from src.parser.yclients_parser import YClientsParser
print('✅ All imports successful')
"

# Run unit tests
python -m pytest tests/test_parser_units.py -v
# Expected: 15 passed

# Run regression tests
python -m pytest tests/test_no_demo_data.py -v  
# Expected: 7 passed
```

### **Step 2: Verify URL Routing**
```bash
# Test URL detection logic
python -c "
import sys
sys.path.append('.')
from src.parser.parser_router import ParserRouter
from unittest.mock import Mock

router = ParserRouter(Mock())

# Test Pavel's URLs
urls = [
    'https://n1165596.yclients.com/company/1109937/record-type?o=',
    'https://n1308467.yclients.com/company/1192304/record-type?o=',
    'https://example.com/booking'  # Non-YClients
]

for url in urls:
    is_yclients = router.is_yclients_url(url)
    print(f'📍 {url[:50]}... → {"Playwright" if is_yclients else "Lightweight"}')
"
```

### **Step 3: Database Setup**
```bash
# Initialize Supabase database
python -c "
import asyncio
import os
from src.database.db_manager import DatabaseManager

async def init_db():
    db = DatabaseManager()
    await db.initialize()
    print('✅ Database initialized')

# Set your real Supabase credentials first
os.environ['SUPABASE_URL'] = 'https://your-project.supabase.co'
os.environ['SUPABASE_KEY'] = 'your_key'

asyncio.run(init_db())
"
```

### **Step 4: Production Start**
```bash
# Start the full system
python lightweight_parser.py

# Expected output:
# ✅ SUPABASE INTEGRATION: Загружен DatabaseManager
# ✅ PARSER ROUTER: Загружен ParserRouter
# 🏁 ГОТОВНОСТЬ К ПРОДАКШН: ✅ ДА
```

---

## 🔍 **Verification & Testing**

### **Health Check Endpoints**
```bash
# System status
curl http://localhost:8000/

# Parser status  
curl http://localhost:8000/parser/status

# Trigger manual parsing
curl -X POST http://localhost:8000/parser/run

# Check extracted data
curl http://localhost:8000/api/booking-data
```

### **Success Indicators**

#### **Logs Should Show:**
```
🚀 Запуск улучшенного парсера с маршрутизацией...
🎯 Обработка URL: https://n1165596.yclients.com/company/1109937/record-type?o=
🎯 Routing to Playwright parser: https://n1165596...
INFO: Step 1: Service selection
INFO: Step 2: Court selection - Found Корт №1
INFO: Step 3: Date/time selection - Found 15:00
INFO: Step 4: Price extraction - Found 6000 ₽
✅ Extracted 15 records from https://n1165596...
```

#### **Database Should Contain:**
```json
{
  "venue_name": "Нагатинская",
  "court_name": "Корт №1 Ультрапанорамик", 
  "price": "6000 ₽",
  "time": "15:00",
  "duration": 60,
  "extracted_at": "2025-08-11T..."
}
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. "Executable doesn't exist" Error**
```bash
# Install Playwright browsers
playwright install chromium

# Verify installation
playwright --version
```

#### **2. "Invalid URL" Database Error**
```bash
# Check environment variables
echo "SUPABASE_URL: $SUPABASE_URL"
echo "SUPABASE_KEY: ${SUPABASE_KEY:0:20}..."

# Test database connection
python -c "
from src.database.db_manager import DatabaseManager
import asyncio

async def test_db():
    db = DatabaseManager()
    await db.initialize()
    
asyncio.run(test_db())
"
```

#### **3. No Data Extracted**
```bash
# Check URL accessibility
curl -I https://n1165596.yclients.com/company/1109937/record-type?o=

# Run single URL test
python -c "
import asyncio
from src.parser.parser_router import ParserRouter
from unittest.mock import Mock

async def test_single():
    router = ParserRouter(Mock())
    url = 'https://n1165596.yclients.com/company/1109937/record-type?o='
    print(f'Testing: {router.is_yclients_url(url)}')

asyncio.run(test_single())
"
```

#### **4. Demo Data Found**
```bash
# Run regression tests
python -m pytest tests/test_no_demo_data.py -v

# Check for demo data in results
curl http://localhost:8000/api/booking-data | grep -c "Ультрапанорамик"
# Should be 0 unless parsing real Нагатинская venue
```

---

## 📊 **Monitoring & Maintenance**

### **Performance Monitoring**
- **Parser runs every 10 minutes** (configurable via PARSE_INTERVAL)
- **Each URL parsing takes ~30-60 seconds** (due to 4-step navigation)
- **Memory usage**: ~100-200MB per browser instance
- **Database writes**: Batch inserts for efficiency

### **Log Files**
- **Parser logs**: Check console output or configure file logging
- **Error tracking**: Failed URLs logged with details
- **Performance metrics**: Timing information for each step

### **Regular Maintenance**
```bash
# Weekly: Update Playwright browsers
playwright install chromium

# Monthly: Check for Python dependency updates
pip list --outdated

# As needed: Clear browser cache
rm -rf ~/.cache/ms-playwright/
playwright install chromium
```

---

## ✅ **Deployment Checklist**

- [ ] **Environment variables set** (API_KEY, SUPABASE_URL, SUPABASE_KEY, PARSE_URLS)
- [ ] **Dependencies installed** (playwright, supabase, etc.)
- [ ] **Browsers installed** (`playwright install chromium`)
- [ ] **Database connection working** (can connect to Supabase)
- [ ] **Unit tests passing** (15/15 tests pass)
- [ ] **Regression tests passing** (7/7 tests pass)
- [ ] **URL routing verified** (YClients → Playwright, Others → Lightweight)
- [ ] **Health endpoints responding** (GET /, /parser/status)
- [ ] **Background scheduler active** (runs every PARSE_INTERVAL)
- [ ] **Real data extraction confirmed** (no demo data in results)

---

## 🎯 **Production URLs**

Pavel's real venue URLs are configured and ready:

1. **Нагатинская** (Working reference): `n1165596.yclients.com`
2. **Корты-Сетки** (Tennis): `n1308467.yclients.com`  
3. **Padel Friends** (Padel): `b861100.yclients.com`
4. **ТК Ракетлон** (Tennis): `b1009933.yclients.com`
5. **Padel A33** (Padel): `b918666.yclients.com`

All URLs will automatically use the 4-step Playwright navigation to extract real booking data.

**🚀 System is production-ready with zero demo data fallbacks!**