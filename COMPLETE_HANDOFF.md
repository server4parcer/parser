# COMPLETE HANDOFF - YClients Parser Project

**Date**: 2025-11-08
**Status**: Price capture working, Provider field broken
**Next Task**: Fix provider selector

---

## PROJECT CONTEXT

### Business Goal
Client Pavel needs to scrape YClients booking data for venue b861100 (Padel Friends) to track:
- Court availability (dates/times)
- Prices per time slot
- Which court/provider (court names like "Корт 3")
- Export to CSV for analysis

### Critical Data Fields Required
1. **date** - Booking date
2. **time** - Booking time slot
3. **price** - Price with ₽ symbol
4. **provider** - Court/provider name (e.g., "Корт 3 (для игры 1х1)")
5. **seat_number** - Court number (optional, can derive from provider)

---

## WHAT PREVIOUS AGENTS DID

### Session 1 (Nov 7-8): Found Root Cause
- **Problem**: Current dates (Nov 7-8) have NO availability
- **Discovery**: Page shows "В этот день нет свободного времени" (No free time today)
- **Solution Found**: Page has button "Перейти к ближайшей дате" (Go to nearest date)
- **Verified Flow** using Playwright MCP:
  ```
  1. Click "Перейти к ближайшей дате" button
  2. Time slots appear (9:00, 22:00, 22:30)
  3. Click time slot → "Продолжить" button appears
  4. Click "Продолжить" → Service page with PRICES
  5. Found: Provider "Корт 3 (для игры 1х1)", Price "1,200 ₽"
  ```

### Session 2 (Nov 8): Implemented Flow
- **Fixed**: Button click with `force=True` (Angular overlay issue)
- **Fixed**: Time slot selector using `get_by_text(re.compile(r'^\d{1,2}:\d{2}$'))`
- **Working**: Full navigation flow
- **Working**: Price capture (1 200 ₽)
- **Broken**: Provider selector times out

### Current Status
```
✅ Price: 1 200 ₽
✅ Date: 2025-11-10
✅ Time: 09:00:00
❌ Provider: Unknown (should be "Корт 3 (для игры 1х1)")
```

---

## CURRENT CODE STATE

### Working Code Path (src/parser/yclients_parser.py)

**Lines 1022-1097**: `handle_time_selection_page` method

**Flow that works**:
```python
# Line 1026: Click nearest date button
await nearest_date_btn.click(force=True)
await page.wait_for_timeout(3000)

# Line 1032-1036: Find and click time slot
time_slots = await page.get_by_text(re.compile(r'^\d{1,2}:\d{2}$')).all()
time_slot = time_slots[0]
time_text = await time_slot.text_content()
await time_slot.click(force=True)

# Line 1043-1046: Click Продолжить
continue_btn = page.get_by_role('button', name='Продолжить')
await continue_btn.click(force=True)
await page.wait_for_load_state('networkidle', timeout=10000)

# Line 1050: Check we're on service page
if 'select-services' in page.url:
```

**Lines 1051-1058**: BROKEN PROVIDER CAPTURE
```python
# Get provider (paragraph element)
provider = 'Unknown'
try:
    provider_el = page.locator('paragraph').first  # ❌ THIS TIMES OUT
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

**Lines 1062-1089**: WORKING PRICE CAPTURE
```python
price_elements = await page.get_by_text(re.compile(r'\d+[,\s]*\d*\s*₽')).all()
logger.info(f"💰 Found {len(price_elements)} prices")

for price_el in price_elements:
    price_text = await price_el.text_content()
    price_clean = price_text.strip()

    result = {
        'url': page.url,
        'date': suggested_date,
        'time': time_text.strip(),
        'provider': provider,  # ❌ This is "Unknown"
        'price': price_clean,  # ✅ This works: "1 200 ₽"
        # ...
    }
    results.append(result)
```

---

## THE PROBLEM IN DETAIL

### Why Provider is "Unknown"

When we land on the service page (`select-services`), we try:
```python
provider_el = page.locator('paragraph').first
```

This selector **doesn't exist** or **times out** on the YClients service page.

### What We Know From Previous Testing

From Playwright MCP exploration (Nov 7-8), we VERIFIED that:
- The service page DOES show provider text
- Text found: "Корт 3 (для игры 1х1)"
- This text is visible on the page
- The price "1,200 ₽" is on the SAME page

**Conclusion**: If price is there, provider is there too. Just need the right selector.

---

## YOUR TASK

### Goal
Change line 1053 in `src/parser/yclients_parser.py` from:
```python
provider_el = page.locator('paragraph').first
```

To the correct selector that captures "Корт 3 (для игры 1х1)".

### Method: Use Playwright MCP to Inspect Page

#### Step 1: Navigate to Service Page

Start browser:
```
mcp__playwright__browser_navigate
url: https://b861100.yclients.com/company/804153/personal/select-time?o=m-1
```

Click nearest date button:
```
mcp__playwright__browser_click
element: button containing "Перейти"
ref: (from snapshot)
```

Click time slot:
```
mcp__playwright__browser_click
element: text "9:00" or "22:00"
ref: (from snapshot)
```

Click Продолжить:
```
mcp__playwright__browser_click
element: button "Продолжить"
ref: (from snapshot)
```

#### Step 2: Inspect Service Page

Take snapshot:
```
mcp__playwright__browser_snapshot
```

Look for:
- Text containing "Корт 3" or "Корт"
- Element that has the provider name
- Note the element type (ui-kit-headline, ui-kit-body, h1, div, etc.)

#### Step 3: Test Selectors

Use JavaScript to find the element:
```
mcp__playwright__browser_evaluate
function: () => {
    // Try YClients UI kit elements
    const headline = document.querySelector('ui-kit-headline');
    if (headline) return {type: 'ui-kit-headline', text: headline.textContent};

    const body = document.querySelector('ui-kit-body');
    if (body) return {type: 'ui-kit-body', text: body.textContent};

    // Try headings
    const h1 = document.querySelector('h1');
    if (h1) return {type: 'h1', text: h1.textContent};

    // Find any element with "Корт"
    const all = Array.from(document.querySelectorAll('*'));
    const withKort = all.find(el => el.textContent.includes('Корт'));
    if (withKort) return {type: withKort.tagName, text: withKort.textContent, class: withKort.className};

    return 'Not found';
}
```

This will tell you which selector to use.

#### Step 4: Update Code

File: `src/parser/yclients_parser.py`
Line: 1053

Change to the selector that worked:
```python
# If ui-kit-headline worked:
provider_el = page.locator('ui-kit-headline').first

# If ui-kit-body worked:
provider_el = page.locator('ui-kit-body').first

# If h1 worked:
provider_el = page.locator('h1').first

# Or whatever element type worked in Step 3
```

---

## TESTING YOUR FIX

### Local Test

```bash
cd /Users/m/git/clients/yclents/yclients-local-fix

export SUPABASE_URL="https://zojouvfuvdgniqbmbegs.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpvam91dmZ1dmRnbmlxYm1iZWdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDMyNDgzMCwiZXhwIjoyMDc1OTAwODMwfQ.D9tQNYmStQ9EddTnxQL-N1hmmCs9CTIJgRp6qhmSJCc"

# Clear old test data
python3 -c "from supabase import create_client; c=create_client('https://zojouvfuvdgniqbmbegs.supabase.co', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpvam91dmZ1dmRnbmlxYm1iZWdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDMyNDgzMCwiZXhwIjoyMDc1OTAwODMwfQ.D9tQNYmStQ9EddTnxQL-N1hmmCs9CTIJgRp6qhmSJCc'); c.table('booking_data').delete().neq('id',0).execute(); print('✅ Cleared old data')"

# Run test
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

    # Save to Supabase
    if data:
        await db.save_booking_data(url, data)

    await parser.close()
    await db.close()

    print(f'\n=== TEST RESULTS ===')
    print(f'Success: {success}')
    print(f'Records: {len(data)}')
    if data:
        for r in data:
            print(f'Provider: {r.get(\"provider\")}')
            print(f'Price: {r.get(\"price\")}')
            print(f'Date: {r.get(\"date\")}')
            print(f'Time: {r.get(\"time\")}')

asyncio.run(test())
"
```

### Expected Output (BEFORE FIX):
```
Provider: Unknown
Price: 1 200 ₽
```

### Expected Output (AFTER FIX):
```
Provider: Корт 3 (для игры 1х1)
Price: 1 200 ₽
```

### Verify in Supabase

```bash
./check_supabase_data.sh
```

Should show:
```
Date: 2025-11-10 | Time: 09:00:00
Price: 1 200 ₽ | Provider: Корт 3 (для игры 1х1)
```

NOT:
```
Provider: Unknown
```

---

## DEPLOYMENT PROCESS

### After Fix is Verified Locally

```bash
git add src/parser/yclients_parser.py
git commit -m "Fix provider selector to capture court name from service page"
git push origin main
```

### TimeWeb Auto-Deploy
- GitHub webhook triggers TimeWeb
- TimeWeb pulls from main branch
- Docker container rebuilds
- Parser starts running every 10 minutes

### Verify TimeWeb Logs

Look for:
```
✅ [PRODUCTION-PROOF] PRICE CAPTURED: 1 200 ₽
✅ [PRODUCTION-PROOF] Full record: date=2025-11-10, time=9:00, provider=Корт 3 (для игры 1х1), price=1 200 ₽
✅ [PRODUCTION-PROOF] SAVED TO SUPABASE: 1 records
```

If you see "provider=Unknown" in logs, the fix didn't work.

---

## IMPORTANT CONTEXT FROM PAST SESSIONS

### Why We Need force=True on Clicks
YClients uses Angular framework with overlays. Normal clicks fail with:
```
<span class="y-core-button__text">… intercepts pointer events
```

Solution: Use `force=True` on all clicks.

### Why Some Dates Don't Work
Current dates (Nov 7-8) have no availability. The "nearest date" button navigates to the first available date (usually 2 days ahead).

### Why We Use Regex for Time Slots
Time slots are in `generic` or text elements with format "9:00", "22:00", etc.
Selector: `page.get_by_text(re.compile(r'^\d{1,2}:\d{2}$'))`

### Why We Use Regex for Prices
Prices have format "1 200 ₽" or "1,200 ₽" (with spaces/commas).
Selector: `page.get_by_text(re.compile(r'\d+[,\s]*\d*\s*₽'))`

### Page Flow is Different Per Venue
Some YClients venues have:
- TIME → COURT → SERVICE (3 steps)

This venue (b861100) has:
- TIME → SERVICE (2 steps, direct)

That's why we land directly on service page after clicking Продолжить.

---

## FILES YOU NEED TO KNOW

### Core Files
```
yclients-local-fix/
├── src/
│   ├── parser/
│   │   └── yclients_parser.py           # LINE 1053 - FIX HERE
│   ├── database/
│   │   └── db_manager.py                # Handles Supabase saves
│   └── main.py                          # Entry point
├── check_supabase_data.sh               # Quick check script
├── FINAL_WORKING_SOLUTION.md            # Original verified flow
├── DEPLOYMENT_READY.md                  # Deployment status
└── CLAUDE.md                            # Business requirements
```

### Config Files
```
.env                                     # Supabase credentials (local)
config/settings.py                       # App settings
requirements.txt                         # Python dependencies
Dockerfile                               # TimeWeb deployment
```

### Supabase Setup
- **URL**: https://zojouvfuvdgniqbmbegs.supabase.co
- **Table**: booking_data
- **Columns**: id, url_id, url, date, time, price, provider, seat_number, location_name, court_type, time_category, duration, created_at, updated_at

---

## WHAT CLIENT PAVEL NEEDS (END GOAL)

### Final CSV Should Look Like:
```csv
date,time,price,provider,seat_number,location_name
2025-11-10,09:00:00,1 200 ₽,Корт 3 (для игры 1х1),3,Padel Friends
2025-11-10,22:00:00,1 200 ₽,Корт 3 (для игры 1х1),3,Padel Friends
2025-11-11,09:00:00,2 400 ₽,Корт 1 (для игры 2х2),1,Padel Friends
```

### Current CSV Shows:
```csv
date,time,price,provider,seat_number,location_name
2025-11-10,09:00:00,1 200 ₽,Unknown,,,
```

**Just need to fix provider field!** Everything else can be derived:
- `seat_number`: Extract "3" from "Корт 3"
- `location_name`: Get from URL or venue context

---

## TROUBLESHOOTING

### If Provider Still Shows "Unknown"

1. **Check logs** for:
   ```
   ⚠️ Failed to get provider: Locator.text_content: Timeout
   ```
   Means selector is wrong.

2. **Use Playwright MCP** to inspect page again:
   ```
   mcp__playwright__browser_evaluate
   function: () => document.body.innerHTML
   ```
   Search HTML for "Корт" to find the element.

3. **Try fallback**: Get all page text and regex extract:
   ```python
   all_text = await page.locator('body').text_content()
   import re
   match = re.search(r'Корт \d+ \([^)]+\)', all_text)
   if match:
       provider = match.group()
   ```

### If Price Stops Working
Don't touch price code! It's working. If it breaks, check:
- Did you modify lines 1062-1089? Revert.
- Are you on the service page? Check `page.url` contains "select-services"

### If Test Hangs
- Headless browser issue. Add timeout to test script.
- Or run with visible browser: Set `headless=False` in browser_manager.py

---

## SUMMARY FOR QUICK START

1. **Problem**: Provider = "Unknown", should be "Корт 3 (για игры 1х1)"
2. **File**: `src/parser/yclients_parser.py` line 1053
3. **Method**: Use Playwright MCP → inspect page → find element with "Корт 3" → update selector
4. **Test**: Run test script → should show provider name, not "Unknown"
5. **Deploy**: `git push origin main` → TimeWeb auto-deploys

**Price already works. Provider is on the page. Just find the right selector.**

---

## LOGS TO WATCH FOR SUCCESS

```
✅ [PRODUCTION-PROOF] PRICE CAPTURED: 1 200 ₽
🏟️ Provider: Корт 3 (для игры 1х1)
✅ [PRODUCTION-PROOF] Full record: date=2025-11-10, time=9:00, provider=Корт 3 (для игры 1х1), price=1 200 ₽
✅ [PRODUCTION-PROOF] SAVED TO SUPABASE: 1 records
```

If you see:
```
⚠️ Failed to get provider: Locator.text_content: Timeout
```

Then selector is still wrong.

---

**STATUS**: Ready for provider field fix
**TIME ESTIMATE**: 30-60 min (inspect page + update selector + test)
**PRIORITY**: HIGH - Client waiting for complete data
