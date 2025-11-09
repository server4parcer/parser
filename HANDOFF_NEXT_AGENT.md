# 🎯 HANDOFF FOR NEXT AGENT - Data Quality Fix Required

**Date**: 2025-11-08
**Status**: ⚠️ PRICE CAPTURE WORKING - PROVIDER DATA MISSING
**Priority**: HIGH - Client Pavel needs complete data

---

## ✅ What's Working

### Price Capture - SUCCESS ✅
```
Price: 1 200 ₽
Date: 2025-11-10
Time: 09:00:00
```

**Proof in code**:
- File: `src/parser/yclients_parser.py`
- Lines: 1050-1097
- Status: ✅ Capturing prices successfully

---

## ❌ What's MISSING - CRITICAL

### Provider Field Shows "Unknown" ❌

**Current CSV Export**:
```csv
date,time,price,provider,seat_number,location_name
2025-11-10,09:00:00,1 200 ₽,Unknown,,,
```

**Expected Data** (from Playwright MCP testing):
```
Provider: "Корт 3 (для игры 1х1)"
Price: "1 200 ₽"
```

### Root Cause

**File**: `src/parser/yclients_parser.py`
**Line**: 1053-1058

```python
provider = 'Unknown'
try:
    provider_el = page.locator('paragraph').first
    provider = await provider_el.text_content()
    provider = provider.strip()
    logger.info(f"🏟️ Provider: {provider}")
except Exception as e:
    logger.warning(f"⚠️ Failed to get provider: {e}")
```

**Error in logs**:
```
⚠️ Failed to get provider: Locator.text_content: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("paragraph").first
```

**Issue**: The `paragraph` selector doesn't exist or times out on the service page.

---

## 🔧 FILES TO READ FOR FIX

### 1. Verified Working Flow Document
**File**: `FINAL_WORKING_SOLUTION.md`
**Lines to read**: ALL (182 lines)
**Why**: Contains exact selectors that worked in Playwright MCP testing

### 2. Current Parser Implementation
**File**: `src/parser/yclients_parser.py`
**Lines to read**: 1002-1097 (handle_time_selection_page method)
**Why**: This is where the provider scraping happens

### 3. Live Browser Findings
**File**: `LIVE_FLOW_VERIFIED_2025-11-08.md`
**Lines to read**: ALL (if exists)
**Why**: Contains DOM structure from actual page inspection

---

## 🎯 TASK FOR NEXT AGENT

### Primary Goal
Fix provider field to capture "Корт 3 (для игры 1х1)" instead of "Unknown"

### Step-by-Step Plan

#### Phase 1: Research (Use Playwright MCP)
```bash
# Navigate to service page and inspect DOM
1. Click "Перейти к ближайшей дате" button
2. Click time slot "9:00"
3. Click "Продолжить"
4. You're now on select-services page
5. Use browser_snapshot to see all elements
6. Find the element containing "Корт 3 (для игры 1х1)"
```

#### Phase 2: Find Correct Selector
Look for these possibilities:
- `ui-kit-headline` - YClients uses this for titles
- `ui-kit-body` - For descriptive text
- First text element on page
- Element with data-testid or similar
- h1, h2, h3 tags
- div with specific class

#### Phase 3: Update Code
**File**: `src/parser/yclients_parser.py`
**Line**: 1053-1058

Replace:
```python
provider_el = page.locator('paragraph').first
```

With correct selector found in Phase 2.

#### Phase 4: Test
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
    print(f'\nRecords: {len(data)}')
    for r in data:
        print(f'Provider: {r.get(\"provider\")} | Price: {r.get(\"price\")}')

asyncio.run(test())
"
```

**Expected output**:
```
Provider: Корт 3 (для игры 1х1) | Price: 1 200 ₽
```

---

## 📋 Complete Data Requirements (Client Pavel)

According to `CLAUDE.md` in yclients-local-fix folder:

### MUST HAVE (Critical):
1. ✅ **date** - Working (2025-11-10)
2. ✅ **time** - Working (09:00:00)
3. ✅ **price** - Working (1 200 ₽)
4. ❌ **provider** - BROKEN (shows "Unknown", need "Корт 3 (для игры 1х1)")
5. ❌ **seat_number** - Missing (need "3" or "А33")

### NICE TO HAVE (Optional):
6. ⚠️ **location_name** - Empty (could derive from URL: "Padel Friends")
7. ⚠️ **court_type** - Empty (could be "PADEL" based on service)
8. ✅ **time_category** - Working (MORNING)
9. ✅ **duration** - Working (60)

---

## 🔍 Known Working Code Snippets

### From FINAL_WORKING_SOLUTION.md

This selector worked in testing:
```python
# Get provider (paragraph element)
provider_el = page.locator('paragraph').first
provider = await provider_el.text_content()
```

But logs show it times out, so we need alternative selectors.

### Alternative Selectors to Try

Based on YClients patterns:
```python
# Option 1: ui-kit-headline (YClients standard)
provider_el = await page.locator('ui-kit-headline').first

# Option 2: ui-kit-body
provider_el = await page.locator('ui-kit-body').first

# Option 3: First visible text
provider_el = await page.locator('h1, h2, h3').first

# Option 4: Get all text and find court pattern
all_text = await page.locator('body').text_content()
import re
court_match = re.search(r'Корт \d+[^,]*', all_text)

# Option 5: JavaScript extraction
provider = await page.evaluate('''() => {
    const texts = Array.from(document.querySelectorAll('*'))
        .map(el => el.textContent)
        .filter(t => t.includes('Корт'));
    return texts[0] || 'Unknown';
}''')
```

---

## 🚀 Quick Test Commands

### 1. Check current Supabase data:
```bash
./check_supabase_data.sh
```

### 2. Clear test data before new test:
```bash
python3 -c "from supabase import create_client; c=create_client('https://zojouvfuvdgniqbmbegs.supabase.co', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpvam91dmZ1dmRnbmlxYm1iZWdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDMyNDgzMCwiZXhwIjoyMDc1OTAwODMwfQ.D9tQNYmStQ9EddTnxQL-N1hmmCs9CTIJgRp6qhmSJCc'); c.table('booking_data').delete().neq('id',0).execute(); print('Cleared')"
```

### 3. Use Playwright MCP to inspect page:
```
1. Use browser_navigate to URL
2. Click nearest date button
3. Click time slot
4. Click Продолжить
5. Use browser_snapshot to see all elements
6. Find provider text element
```

---

## 📊 Success Criteria

### Before:
```csv
date,time,price,provider,seat_number
2025-11-10,09:00:00,1 200 ₽,Unknown,
```

### After (GOAL):
```csv
date,time,price,provider,seat_number
2025-11-10,09:00:00,1 200 ₽,Корт 3 (для игры 1х1),3
```

---

## 🎯 Minimal Scope for This Session

**ONLY** fix the provider field. Don't:
- Change price capture (it works!)
- Modify button clicking logic (it works!)
- Refactor database code
- Change logging (it's good)

**JUST** find and fix the provider selector on lines 1053-1058.

---

## 📁 File Locations Summary

```
yclients-local-fix/
├── src/
│   ├── parser/
│   │   └── yclients_parser.py          # Lines 1053-1058 - FIX HERE
│   └── database/
│       └── db_manager.py                # Don't touch
├── FINAL_WORKING_SOLUTION.md            # Read for context
├── LIVE_FLOW_VERIFIED_2025-11-08.md    # Read for DOM structure
├── check_supabase_data.sh               # Test script
└── CLAUDE.md                            # Business requirements
```

---

## ⚡ Priority Order

1. **HIGH**: Fix provider field (Unknown → "Корт 3 (для игры 1х1)")
2. **MEDIUM**: Extract seat_number from provider (derive "3" from "Корт 3")
3. **LOW**: Add location_name, court_type (can derive from context)

Focus on #1 first - get the provider name working!

---

**STATUS**: Ready for next agent to fix provider field selector
**TIME ESTIMATE**: 30-60 minutes (research + fix + test)
