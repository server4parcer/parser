# 🚨 HANDOFF: Provider Field Not Capturing Court Names

**Date**: 2025-11-08
**Status**: Prices working ✅ | Provider broken ❌
**Urgency**: HIGH - 0% client-ready data quality

---

## ⚡ START HERE: Token-Efficient Guide

**Read this first**: `EXACT_FILES_TO_READ.md`

Contains:
- Exact file paths and line ranges (no exploration needed)
- 13-minute workflow
- Only ~50 lines of code to read
- Ready-to-copy test commands

**This file** contains full context and background.

---

## ❌ Current Problem

### Data Quality Analysis:
```
Total records: 22
✅ Good (price + provider): 0 (0%)
⚠️  Has price, missing provider: 17 (77%)
❌ Missing both: 5 (23%)

CLIENT-READY QUALITY: 0%
```

### What's Working:
- ✅ Prices captured: "1 200 ₽", "2 000 ₽", "4 000 ₽"
- ✅ Dates: 2025-11-10 (correct future dates)
- ✅ Times: 09:00, 22:00 (different slots)
- ✅ Data saved to Supabase
- ✅ TimeWeb running automatically every ~20 minutes

### What's Broken:
- ❌ **Provider: "Unknown"** instead of "Корт 3 (для игры 1х1)"
- ❌ 5 records with "Цена не найдена" (from url_id=2, different flow)
- ❌ Empty fields: seat_number, location_name, url

---

## 🔍 Root Cause

**File**: `yclients-local-fix/src/parser/yclients_parser.py`
**Lines**: 1050-1058

### Current Code (FAILING):
```python
# Get provider (paragraph element)
provider = 'Unknown'
try:
    provider_el = page.locator('paragraph').first
    provider = await provider_el.text_content()
    provider = provider.strip()
    logger.info(f"🏟️ Provider: {provider}")
except Exception as e:
    logger.warning(f"⚠️ Failed to get provider: {e}")
```

### Error in Logs:
```
⚠️ Failed to get provider: Locator.text_content: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("paragraph").first
```

**Why it fails**: The selector `paragraph` doesn't exist or times out on the service page.

---

## ✅ Verified Working Flow

From Playwright MCP testing (2025-11-08):

1. Click "Перейти к ближайшей дате" ✅
2. Time slots appear: 9:00, 22:00, 22:30 ✅
3. Click time → "Продолжить" appears ✅
4. Click "Продолжить" → Service page loads ✅
5. **FAIL HERE**: Provider selector times out ❌

**Expected data from handoff**:
- Provider: "Корт 3 (для игры 1х1)"
- Price: "1,200 ₽"

---

## 🔧 What Needs to be Fixed

### Task 1: Fix Provider Selector

**Current**: `page.locator('paragraph').first`
**Need to**: Find correct selector for court name on service page

**Approach**:
1. Use Playwright MCP to navigate to service page:
   ```
   URL: https://b861100.yclients.com/.../select-services
   ```

2. Inspect page to find court name element:
   ```python
   # Try these selectors:
   - page.locator('[class*="court"]')
   - page.locator('[class*="provider"]')
   - page.locator('h1, h2, h3').first
   - page.get_by_text(re.compile(r'Корт'))
   ```

3. Test selector captures "Корт 3 (для игры 1х1)"

4. Update code at line 1053 with working selector

### Task 2: Fix Bad Records (url_id=2)

These records show:
- Date: 2025-11-08 (today, not future)
- Time: 14:00
- Price: "Цена не найдена"
- Provider: "Не указан"

**Why**: Different URL or flow not handling "nearest date" button

**Fix**:
1. Check what url_id=2 is (query urls table)
2. Either fix that flow or disable that URL
3. Ensure all URLs use "nearest date" flow

### Task 3: Populate Missing Fields

**Empty fields**:
- `url` - Should store source URL
- `seat_number` - Extract from provider (e.g., "Корт 3" → "3")
- `location_name` - Store venue name

**Code location**: `src/parser/yclients_parser.py` lines 1073-1086

---

## 📊 Test Data to Verify Fix

**Current (BAD)**:
```csv
date,time,price,provider
2025-11-10,09:00:00,1 200 ₽,Unknown
```

**Expected (GOOD)**:
```csv
date,time,price,provider,seat_number,location_name
2025-11-10,09:00:00,1 200 ₽,Корт 3 (для игры 1х1),3,Padel Friends
```

---

## 🧪 How to Test Fix

### 1. Local Test:
```bash
cd /Users/m/git/clients/yclents/yclients-local-fix

export SUPABASE_URL="https://zojouvfuvdgniqbmbegs.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpvam91dmZ1dmRnbmlxYm1iZWdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDMyNDgzMCwiZXhwIjoyMDc1OTAwODMwfQ.D9tQNYmStQ9EddTnxQL-N1hmmCs9CTIJgRp6qhmSJCc"

venv/bin/python3 -c "
import asyncio, sys
sys.path.insert(0, '/Users/m/git/clients/yclents/yclients-local-fix')
from src.database.db_manager import DatabaseManager
from src.parser.yclients_parser import YClientsParser

async def test():
    db = DatabaseManager()
    await db.initialize()
    url = 'https://b861100.yclients.com/company/804153/personal/select-time?o=m-1'
    parser = YClientsParser([url], db)
    await parser.initialize()
    success, data = await parser.parse_url(url)
    await parser.close()
    await db.close()

    print(f'Records: {len(data)}')
    for r in data[:1]:
        print(f'Provider: {r.get(\"provider\")}')
        print(f'Price: {r.get(\"price\")}')
        assert r.get('provider') != 'Unknown', 'Provider still Unknown!'
        assert 'Корт' in r.get('provider', ''), 'Provider should contain Корт'
        print('✅ TEST PASSED')

asyncio.run(test())
"
```

**Expected output**:
```
Provider: Корт 3 (для игры 1х1)
Price: 1 200 ₽
✅ TEST PASSED
```

### 2. Check Supabase:
```bash
./check_supabase_data.sh
```

Look for latest record with:
- `provider` != "Unknown"
- `provider` contains "Корт"

### 3. Verify TimeWeb:
After push to GitHub, check TimeWeb logs for:
```
✅ [PRODUCTION-PROOF] Full record: provider=Корт 3 (для игры 1х1), price=1 200 ₽
```

---

## 📁 Files to Read

### Essential:
1. `src/parser/yclients_parser.py` - Lines 1050-1097 (service page scraping)
2. `FINAL_WORKING_SOLUTION.md` - Original verified selectors
3. `LIVE_FLOW_VERIFIED_2025-11-08.md` - Playwright exploration findings

### Reference:
4. Current CSV: `supabase_export_20251108_213444.csv` - Shows bad data
5. Database schema: `src/database/db_manager.py` - clean_booking_data() function

---

## 🎯 Success Criteria

**Before (Current)**:
- Client-ready quality: 0%
- Provider: "Unknown" (17/22 records)
- Bad records: 5/22 (23%)

**After (Target)**:
- Client-ready quality: 95%+
- Provider: "Корт X (для игры 1х1)" format
- Bad records: 0

**Deliverable**:
- CSV export with all fields populated
- No "Unknown" providers
- No "Цена не найдена" prices

---

## 🚀 Deployment Process

1. Fix provider selector (Task 1)
2. Test locally - verify provider captured
3. Commit with message: "Fix: Capture court names in provider field"
4. Push to GitHub main branch
5. TimeWeb auto-deploys
6. Wait 20 minutes for new data
7. Run `./check_supabase_data.sh`
8. Verify provider field populated

---

## ⏰ Time Estimate

- Task 1 (provider selector): 30 minutes
- Task 2 (fix bad records): 15 minutes
- Task 3 (populate fields): 15 minutes
- Testing: 15 minutes
- **Total**: ~75 minutes

---

**Current Git Commit**: 9e741c3
**Branch**: main
**Last Deploy**: 2025-11-08 ~13:34 UTC

**Next Agent**: Start by using Playwright MCP to navigate to the service page and inspect the provider element. The price selector works, we just need the correct selector for court names.
