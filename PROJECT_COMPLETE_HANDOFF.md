# 📋 YCLIENTS PARSER - COMPLETE PROJECT HANDOFF

## 🎯 PROJECT OVERVIEW

**Project Name**: YClients Parser with Playwright Browser Automation  
**Client**: Pavel  
**Current Status**: Parser working and extracting real data (53,859 records), API partially converted to pure Supabase  
**Repository**: https://github.com/server4parcer/parser  
**Deployment**: TimeWeb Cloud Apps at https://server4parcer-parser-4949.twc1.net  

## 📖 COMPLETE PROJECT HISTORY

### Original Problem (Pavel's Issue)
Pavel reported that the YClients parser was extracting WRONG data:
- Expected prices: 2500₽, 3750₽, 5000₽ for Padel A33 venue
- Expected durations: 60, 90, 120 minutes
- Issue: Parser was returning fake/demo data instead of real YClients data
- TimeWeb container kept exiting with status "Container is not running, status: exited"

### Root Causes Identified
1. **Wrong parser deployed**: E2E test suite was deployed instead of actual parser
2. **Playwright missing**: Container had no browser dependencies
3. **Health check failing**: No `/health` endpoint, container failed health checks
4. **Mixed architecture**: API routes expected PostgreSQL but DatabaseManager used Supabase

### Current Solution Status
✅ **FIXED**: Playwright parser deployed and working  
✅ **FIXED**: 53,859 booking records extracted to Supabase  
✅ **FIXED**: Container running and passing health checks  
❌ **PARTIAL**: API routes partially converted to pure Supabase  
❌ **TODO**: Complete PostgreSQL to Supabase migration  

## 🏗️ DEPLOYMENT ARCHITECTURE

### TimeWeb Cloud Apps Specifics
**URL**: https://server4parcer-parser-4949.twc1.net  
**Server Specs**: 16GB RAM allocated for Playwright browser automation  
**Auto-Deploy**: GitHub push to `main` branch triggers automatic rebuild  
**Build Time**: 2-3 minutes for Docker image with Playwright  
**Container**: Runs on port 8000, nginx proxy handles HTTPS  

### Docker Configuration Details
**File**: `/Users/m/git/clients/yclents/pavel-repo-clean/Dockerfile`
```dockerfile
FROM python:3.10-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers

# TimeWeb-specific requirements - NO VOLUMES ALLOWED
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg ca-certificates git build-essential libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# CRITICAL: Playwright browser installation for TimeWeb
RUN playwright install chromium \
    && playwright install-deps chromium

COPY . .
RUN mkdir -p /app/data /app/logs

EXPOSE 8000

# CRITICAL: Health check uses root endpoint (not /health)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# CRITICAL: Uses src/main.py as entry point
CMD ["python", "src/main.py"]
```

**TimeWeb Restrictions**:
- NO docker-compose.yml support
- NO volumes allowed
- NO USER directives in Dockerfile
- ONLY port 8000 allowed
- Health check REQUIRED for container to stay running

## 🔐 ENVIRONMENT VARIABLES (TimeWeb Panel)

Pavel has configured these in TimeWeb environment variables panel:

```bash
API_KEY=yclients_parser_secure_key_2024
API_HOST=0.0.0.0  
API_PORT=8000
PARSE_URLS=https://b918666.yclients.com/company/855029/personal/menu?o=m-1,[5 more URLs]
PARSE_INTERVAL=600
SUPABASE_URL=https://tfvgbcqjftirclxwqwnr.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRmdmdiY3FqZnRpcmNseHdxd25yIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mjc3Nzk2NywiZXhwIjoyMDY4MzUzOTY3fQ.4szXEDqL7KhQlM3RX89DwiFpIO8LxKRek8-CkTM1-aE
```

**CRITICAL**: All credentials are correctly configured in TimeWeb environment.

## 📁 COMPLETE FILE STRUCTURE & CRITICAL LINES

### Core Application Files

#### `/Users/m/git/clients/yclents/pavel-repo-clean/src/main.py`
**Purpose**: Main entry point for TimeWeb deployment  
**Lines to understand**:
- Lines 30-44: Environment variable fallbacks
- Lines 46-54: Import DatabaseManager and YClientsParser (Playwright-based)
- Lines 60-76: run_api_server() - FastAPI server startup
- Lines 78-124: run_parser() - Playwright parser initialization
- Lines 186-223: main() - Entry point that starts both API and parser
- Lines 225-231: if __main__ block for TimeWeb execution

#### `/Users/m/git/clients/yclents/pavel-repo-clean/src/database/db_manager.py`
**Purpose**: Database connection manager for Supabase  
**Lines to understand**:
- Lines 26-38: __init__ with Supabase URL/key from environment
- Lines 39-82: initialize() method - creates Supabase client
- Lines 407-419: get_booking_data() - retrieves records from Supabase
- **Lines 432-467: POSTGRESQL COMPATIBILITY LAYER (MUST BE REMOVED)**
  - Lines 432-435: @property pool
  - Lines 437-439: async acquire()
  - Lines 441-449: fetchval() method
  - Lines 451-459: fetch() method
  - Lines 461-467: __aenter__/__aexit__ methods
- Lines 469-485: get_statistics() - for /status endpoint

#### `/Users/m/git/clients/yclents/pavel-repo-clean/src/api/routes.py`
**Purpose**: FastAPI REST API endpoints  
**Lines requiring PostgreSQL to Supabase conversion**:

**COMPLETED Conversions**:
- Lines 608-632: `/data` endpoint - CONVERTED to Supabase
- Lines 1047-1052: `/parse` endpoint URL lookup - CONVERTED
- Lines 1101-1110: `/parse/all` URL fetching - CONVERTED

**REMAINING PostgreSQL Queries (MUST CONVERT)**:
- Lines 204-210: URLs list query
- Lines 256-280: URL creation with fetchval/fetchrow
- Lines 326-327: URL fetching by ID
- Lines 384-442: URL update with complex query
- Lines 488-489: URL deletion
- Lines 717-718: Export URL validation
- Lines 791-798: Analytics pricing queries
- Lines 870-877: Analytics availability queries  
- Lines 948-951: Analytics price history queries

#### `/Users/m/git/clients/yclents/pavel-repo-clean/src/parser/yclients_parser.py`
**Purpose**: Playwright browser automation for YClients parsing  
**Key functionality**:
- Lines 10: Uses Playwright for browser automation
- Lines 24-50: __init__ with BrowserManager and ProxyManager
- Lines 51-67: initialize() - starts Playwright browser
- Lines 250-358: navigate_yclients_flow() - 4-step YClients navigation
- Lines 517-634: parse_service_url() - main parsing logic with browser
- Lines 646-696: parse_all_urls() - processes multiple YClients sites

#### `/Users/m/git/clients/yclents/pavel-repo-clean/requirements.txt`
**Purpose**: Python dependencies with Playwright  
```
python-dotenv>=1.0.0
aiohttp>=3.8.4
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
supabase>=1.0.3
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
ujson>=5.8.0
asyncpg>=0.27.0
playwright>=1.54.0
```

## 🧪 TESTING ENDPOINTS

### API Authentication
All endpoints require header: `X-API-Key: yclients_parser_secure_key_2024`

### Working Endpoints
```bash
# Status check (returns Supabase statistics)
curl -H "X-API-Key: yclients_parser_secure_key_2024" \
  https://server4parcer-parser-4949.twc1.net/status

# Response: {"status":"success","message":"Статус парсера получен","data":{"booking_records":53859,"url_records":6,"database_type":"supabase","connected":true}}

# Get booking data
curl -H "X-API-Key: yclients_parser_secure_key_2024" \
  https://server4parcer-parser-4949.twc1.net/data

# Trigger parser for specific URL
curl -X POST -H "X-API-Key: yclients_parser_secure_key_2024" \
  "https://server4parcer-parser-4949.twc1.net/parse?url=https://b918666.yclients.com/company/855029/personal/menu?o=m-1"

# Response: {"status":"success","message":"Парсер запущен для https://b918666.yclients.com/company/855029/personal/menu?o=m-1","data":null}
```

## 🎯 PAVEL'S REQUIREMENTS

### Expected Data
- **Venue**: "Padel A33"
- **Prices**: "2500 ₽", "3750 ₽", "5000 ₽"  
- **Durations**: 60, 90, 120 minutes
- **Database**: Pure Supabase (NO PostgreSQL)
- **Parser**: Playwright browser automation (NOT lightweight HTTP requests)

### Current Status
✅ **Parser working**: 53,859 records extracted from 6 YClients venues  
✅ **Real data**: Actual YClients booking information  
✅ **Supabase connected**: Data being saved correctly  
❌ **API incomplete**: Still has PostgreSQL compatibility layer  

## 🚨 CRITICAL ISSUES TO COMPLETE

### 1. Remove PostgreSQL Compatibility
**File**: `src/database/db_manager.py`  
**Lines to DELETE**: 432-467 (entire PostgreSQL compatibility section)

### 2. Convert Remaining API Routes
**File**: `src/api/routes.py`  
**Pattern to find**: `async with db_manager.pool.acquire() as conn:`  
**Replace with**: Direct Supabase REST API calls

**Conversion Examples**:
```python
# OLD PostgreSQL style:
async with db_manager.pool.acquire() as conn:
    rows = await conn.fetch("SELECT url FROM urls WHERE is_active = TRUE")

# NEW Supabase style:  
response = db_manager.supabase.table("urls").select("url").eq("is_active", True).execute()
rows = response.data or []

# OLD fetchval:
url = await conn.fetchval("SELECT url FROM urls WHERE id = $1", url_id)

# NEW Supabase:
response = db_manager.supabase.table("urls").select("url").eq("id", url_id).execute()
url = response.data[0]["url"] if response.data else None
```

## 📋 COMPLETION CHECKLIST

### Phase 1: Code Cleanup
- [ ] Remove ALL PostgreSQL compatibility methods from `db_manager.py` lines 432-467
- [ ] Convert ALL remaining PostgreSQL queries in `routes.py`
- [ ] Search codebase for: `pool.acquire`, `fetchval`, `fetch`, `fetchrow`
- [ ] Replace with equivalent Supabase REST API calls

### Phase 2: Testing
- [ ] Test `/data` endpoint returns booking records
- [ ] Test `/parse` endpoint triggers new extraction  
- [ ] Test `/status` shows correct statistics
- [ ] Verify all endpoints work with Pavel's API key

### Phase 3: Deployment
- [ ] Commit changes with Russian message: "Завершить миграцию на чистый Supabase"
- [ ] Push to GitHub: `git push origin main`
- [ ] Wait 5-10 minutes for TimeWeb auto-deployment
- [ ] Check TimeWeb logs for successful deployment
- [ ] Test all endpoints post-deployment

### Phase 4: Verification
- [ ] Pavel confirms data visible in Supabase dashboard
- [ ] Parser continues extracting real YClients data
- [ ] No PostgreSQL references remaining in codebase
- [ ] All API endpoints respond correctly

## 🤖 NEXT AGENT INSTRUCTIONS

1. **Start by reading these files**:
   - `src/database/db_manager.py` (focus on lines 432-467)
   - `src/api/routes.py` (search for "pool.acquire")

2. **Search commands to use**:
   ```bash
   grep -n "pool\.acquire" src/api/routes.py
   grep -n "fetchval\|fetch\|fetchrow" src/api/routes.py
   ```

3. **Conversion strategy**:
   - For each PostgreSQL query, identify the table and operation
   - Replace with equivalent `db_manager.supabase.table().method().execute()`
   - Test locally if possible with Pavel's Supabase credentials

4. **Commit guidelines**:
   - Use Russian commit messages
   - Be specific about what was converted
   - Example: "Конвертировать URL management эндпоинты в чистый Supabase"

5. **Testing approach**:
   - Use Pavel's API key: `yclients_parser_secure_key_2024`
   - Test each converted endpoint individually
   - Verify response formats match expected structure

## 🎉 SUCCESS CRITERIA

The project is COMPLETE when:
1. No PostgreSQL references exist in the codebase
2. All API endpoints use pure Supabase REST calls  
3. Pavel can access his 53,859+ booking records via `/data` endpoint
4. Parser continues extracting real YClients data with Playwright
5. All endpoints respond correctly with Pavel's API key
6. Supabase dashboard shows continuous data ingestion

## 📞 DEPLOYMENT CONTACT INFO

**TimeWeb Dashboard**: Pavel has access to container logs and environment variables  
**Supabase Dashboard**: Pavel can verify data ingestion in `booking_data` table  
**GitHub Repository**: https://github.com/server4parcer/parser (auto-deploy enabled)

---

**Document Created**: 2025-09-22  
**Parser Status**: ✅ Working (53,859 records)  
**Completion**: ~85% (API conversion remaining)  
**Next Steps**: Complete PostgreSQL to Supabase migration