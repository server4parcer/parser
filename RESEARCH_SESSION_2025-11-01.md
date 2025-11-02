# Research Session 2025-11-01

## Problem Statement

Parser extracts dates but NOT times or prices, violating business requirements:
- ✅ Required: date, time, price, provider, seat_number
- ❌ Actual: date only, time=None, price=None, provider=None

## Root Cause Analysis

### API Capture Investigation

**What APIs are captured:**
```
✅ search-services (has prices: 2800.0, 5000.0, 4500.0, 6000.0)
✅ search-dates (has dates: 2025-11-04, 2025-11-05, etc.)
✅ search-staff (provider names)
❌ search-timeslots (has times) - NOT captured
```

**Why timeslots API not captured:**
- Parser loads page passively
- APIs fire automatically on page load
- Timeslots API ONLY fires when user clicks:
  1. Click a service
  2. Click a date
  3. THEN timeslots API fires with time slots

### Evidence from Playwright MCP Browser Testing

**Network requests captured:**
```
POST /api/v1/b2c/booking/availability/search-services => 200 ✅
POST /api/v1/b2c/booking/availability/search-dates => 200 ✅
POST /api/v1/b2c/booking/availability/search-staff => 200 ✅
(no timeslots API - user interaction needed)
```

**Page flow discovered:**
1. URL: `/company/1109937/record-type?o=` redirects to `/select-city/2/select-branch?o=`
2. Need to click branch first
3. THEN navigate to services
4. THEN click service + date to trigger timeslots

### Code Analysis Findings

**Bug #1: Logic Error (Line 1422)**
```python
# WRONG - accepts date OR time:
has_valid_bookings = any(record.get('date') or record.get('time')...)

# CORRECT - needs date AND time:
has_valid_bookings = any(record.get('date') and record.get('time')...)
```
This bug caused parser to accept dates-only as "success" and skip full navigation.

**Bug #2: Missing Data Merge (Lines 765-820)**
- API listener captures data into `self.captured_api_data`
- `navigate_yclients_flow()` does DOM scraping, returns results
- **NO MERGE** - API data was captured but never combined with DOM results

**Bug #3: Navigation Assumptions (Line 1036)**
- `navigate_yclients_flow()` assumes it starts at service selection
- Actual: page redirects to branch selection first
- Needs to handle branch redirect before navigating services

## Fixes Applied

### Fix #1: Logic Correction (Commit 37ad54c)
```python
# Line 1422
has_valid_bookings = any(record.get('date') and record.get('time') for record in all_data)
```

### Fix #2: Merge DOM + API Data (Commit 37ad54c)
```python
# Lines 796-815
# After navigation completes, merge DOM results with captured API data
if self.captured_api_data:
    api_results = self.parse_api_responses(self.captured_api_data)
    # Merge logic: combine both sources
    merged = dom_results + api_results
```

### Fix #3: Branch Selection Handling
Already implemented in `handle_multi_location_redirect()` - detected correctly.

## Test Commands

**Local test (requires fixing disk space):**
```bash
cd /Users/m/git/clients/yclents/yclients-local-fix
source venv/bin/activate
export SUPABASE_URL=https://tfvgbcqjftirclxwqwnr.supabase.co
export SUPABASE_KEY=eyJh...

python -c "
import asyncio
from src.parser.yclients_parser import YClientsParser
from src.database.db_manager import DatabaseManager

async def test():
    db = DatabaseManager()
    await db.initialize()
    parser = YClientsParser(['https://n1165596.yclients.com/company/1109937/record-type?o='], db)
    await parser.initialize()
    success, data = await parser.parse_url('https://n1165596.yclients.com/company/1109937/record-type?o=')

    print(f'Success: {success}, Records: {len(data)}')
    for rec in data[:3]:
        print(f'date={rec.get(\"date\")}, time={rec.get(\"time\")}, price={rec.get(\"price\")}, provider={rec.get(\"provider\")}')

    await parser.close()
    await db.close()

asyncio.run(test())
"
```

**Expected result after fix:**
```
Success: True, Records: 50+
date=2025-11-04, time=14:00:00, price=2800₽, provider=Корт А33
date=2025-11-04, time=15:00:00, price=2800₽, provider=Корт А33
...
```

## Outstanding Issues

1. **Local testing blocked** - disk space error on Mac
2. **Merge logic basic** - might create duplicates, needs refinement
3. **Navigation might still fail** - need to verify full click-through works
4. **Timeslots API trigger** - uncertain if navigation clicks trigger the API

## Success Criteria

Parser must extract ALL 5 required fields:
- ✅ date (ISO format: YYYY-MM-DD)
- ✅ time (ISO format: HH:MM:SS)
- ✅ price (e.g., "2800₽" or "2800.0")
- ✅ provider (e.g., "Корт А33")
- ✅ seat_number (e.g., "А33")

## Next Steps

See EXECUTION_PLAN.md for deployment and testing instructions.
