# 🎯 COMPLETE PLAN: Fix Provider Field - Next Agent Instructions

**Date**: 2025-11-08  
**Current Status**: CSV shows provider="Unknown" - need to fix and verify locally before deploy  
**Goal**: Get CSV with provider="Корт 3 (для игры 1х1)" instead of "Unknown"

---

## 📊 ISSUE IDENTIFIED IN CSV

**File**: `supabase_export_20251108_221134.csv`

**Problem** (lines 2-24):
```csv
date,time,price,provider
2025-11-10,09:00:00,1 200 ₽,Unknown  ← ❌ BAD (17 records)
2025-11-10,22:00:00,4 000 ₽,Unknown  ← ❌ BAD
2025-11-08,14:00:00,Цена не найдена,Не указан  ← ❌ BAD (5 records from url_id=2)
```

**Expected**:
```csv
date,time,price,provider
2025-11-10,09:00:00,1 200 ₽,Корт 3 (для игры 1х1)  ← ✅ GOOD
```

---

## 🔍 ROOT CAUSE

**File**: `src/parser/yclients_parser.py`  
**Line**: 1056  
**Issue**: Wrong selector for provider element

**Current code (BROKEN)**:
```python
provider_el = page.locator('paragraph').first  # ← Times out, element not found
```

**Already FIXED to**:
```python
provider_el = page.locator('p.label.category-title').first  # ← Correct selector
```

---

## 📋 COMPLETE EXECUTION PLAN

### PHASE 1: Verify Fix is in Place
**Read these files first (EXACT lines to check)**:

1. **src/parser/yclients_parser.py:1053-1061**
   ```bash
   # Check if fix is applied:
   grep -n "p.label.category-title" src/parser/yclients_parser.py
   # Should return: Line 1056
   ```
   
   **Expected to see**:
   ```python
   1053: # Get provider (court name from category title)
   1054: provider = 'Unknown'
   1055: try:
   1056:     provider_el = page.locator('p.label.category-title').first  ← ✅ MUST BE THIS
   1057:     provider = await provider_el.text_content()
   1058:     provider = provider.strip()
   1059:     logger.info(f"🏟️ Provider: {provider}")
   1060: except Exception as e:
   1061:     logger.warning(f"⚠️ Failed to get provider: {e}")
   ```

2. **If fix NOT in place**: Apply it now using Edit tool on line 1056

---

### PHASE 2: Clear Old Data from Supabase

**Why**: Old "Unknown" data will confuse results  
**Command**:
```bash
cd /Users/m/git/clients/yclents/yclients-local-fix
./clear_supabase.sh
```

**Expected output**:
```
Records before: 23
✅ Deleted records
Records after: 0
✅ Table is now empty - ready for test
```

---

### PHASE 3: Run Parser Locally (Saves to Supabase)

**Environment variables** (already set in script):
```bash
export SUPABASE_URL="https://zojouvfuvdgniqbmbegs.supabase.co"
export SUPABASE_KEY="eyJhbGc...JCc"  # Full key in script
```

**Command**:
```bash
venv/bin/python3 test_provider_fix.py
```

**What this does**:
1. Connects to Supabase ✅
2. Initializes Playwright browser ✅
3. Navigates to: `https://b861100.yclients.com/company/804153/personal/select-time?o=m-1`
4. **Clicks "Перейти к ближайшей дате"** (Go to nearest date)
5. **Clicks time slot** (e.g., 9:00)
6. **Clicks "Продолжить"** (Continue)
7. **Lands on SERVICE PAGE** → Scrapes provider with `p.label.category-title` selector
8. Saves records to Supabase ✅

**Expected output**:
```
================================================================================
TESTING PROVIDER FIELD CAPTURE - LOCAL RUN
================================================================================

1. Initializing database connection...
   ✅ Database connected

2. Testing URL: https://b861100.yclients.com/company/804153/personal/select-time?o=m-1

3. Initializing parser...
   ✅ Parser initialized

4. Running parser (this may take 30-60 seconds)...
   [Navigating to page, clicking buttons, scraping data...]

================================================================================
RESULTS
================================================================================

✅ SUCCESS: Extracted 2 records

First 3 records:
--------------------------------------------------------------------------------

Record 1:
  Date:     2025-11-10
  Time:     09:00:00
  Price:    1,200 ₽
  Provider: Корт 3 (для игры 1х1)  ← ✅ THIS IS THE KEY!
  Service:  Court Rental

Record 2:
  Date:     2025-11-10
  Time:     22:00:00
  Price:    4,000 ₽
  Provider: Корт 3 (для игры 1х1)  ← ✅ GOOD

================================================================================
VALIDATION
================================================================================

✅ TEST PASSED!
   Provider captured correctly: 'Корт 3 (для игры 1х1)'
   Price captured: 1,200 ₽

   The fix is working! Ready to deploy to TimeWeb.

5. Saving to Supabase...
   ✅ Saved 2 records to Supabase

   Run './check_supabase_data.sh' to see the new data!
```

**Duration**: ~30-60 seconds (Playwright navigation)

---

### PHASE 4: Verify Data in Supabase CSV

**Command**:
```bash
./check_supabase_data.sh
```

**Expected output**:
```
================================================================================
SUPABASE DATA CHECK - 2025-11-08 22:XX:XX
================================================================================

Latest 20 records:

1. ID: 36285
   Date: 2025-11-10 | Time: 09:00:00
   Price: 1,200 ₽ | Provider: Корт 3 (для игры 1х1)  ← ✅ GOOD!
   Created: 2025-11-08T22:XX:XX

2. ID: 36286
   Date: 2025-11-10 | Time: 22:00:00
   Price: 4,000 ₽ | Provider: Корт 3 (для игры 1х1)  ← ✅ GOOD!
   Created: 2025-11-08T22:XX:XX

Total records in database: 2

✅ Exported to: supabase_export_20251108_22XXXX.csv
   Total records exported: 2
```

**Then read the CSV**:
```bash
cat supabase_export_20251108_*.csv | tail -5
```

**Expected CSV content**:
```csv
id,url_id,url,date,time,price,provider,...
36285,1,,2025-11-10,09:00:00,1 200 ₽,Корт 3 (для игры 1х1),...  ← ✅
36286,1,,2025-11-10,22:00:00,4 000 ₽,Корт 3 (для игры 1х1),...  ← ✅
```

---

## 🎭 WHEN TO USE PLAYWRIGHT MCP (Optional)

**Use Playwright MCP ONLY if**:
1. Test shows provider="Unknown" again (fix didn't work)
2. Need to inspect the actual page to find NEW selector

**How to use Playwright MCP**:
```python
# Navigate to service page
mcp__playwright__browser_navigate(url="https://b861100.yclients.com/...")

# Click through flow
mcp__playwright__browser_click(element="button", ref="...")

# Take screenshot
mcp__playwright__browser_take_screenshot(filename="debug.png")

# Inspect DOM for provider element
mcp__playwright__browser_evaluate(function='''() => {
  return document.querySelectorAll('p.label.category-title')[0]?.textContent;
}''')
```

**When NOT to use it**:
- If test passes (provider captured correctly)
- For routine testing (use test_provider_fix.py instead)

---

## ✅ ACCEPTANCE CRITERIA (Must ALL pass)

Before deploy to TimeWeb, verify:

- [ ] Line 1056 in `src/parser/yclients_parser.py` has `p.label.category-title` selector
- [ ] `clear_supabase.sh` successfully empties table (0 records)
- [ ] `test_provider_fix.py` runs without errors
- [ ] Test output shows "✅ TEST PASSED!"
- [ ] Provider field contains "Корт" text (NOT "Unknown")
- [ ] `check_supabase_data.sh` shows at least 1 record with provider="Корт..."
- [ ] Latest CSV export has provider column populated correctly
- [ ] Price field also captured (e.g., "1,200 ₽")
- [ ] Date is future date (e.g., 2025-11-10)
- [ ] No records with provider="Unknown" in new data

---

## 🚀 DEPLOYMENT (Only After ALL Criteria Pass)

**DO NOT DEPLOY** until CSV looks correct!

**When ready**:
```bash
git add src/parser/yclients_parser.py
git commit -m "Fix: Capture court names in provider field

Problem: Selector 'paragraph' timing out
Solution: Changed to 'p.label.category-title'
Verified: Local test shows Корт 3 (для игры 1х1) captured

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

**Then wait 30 minutes** for TimeWeb auto-deploy + cron cycle.

---

## 📁 FILES TO READ (Exact Line Ranges)

1. **src/parser/yclients_parser.py:1050-1097**
   - Provider selector code (line 1056 is THE critical line)
   - Price scraping code (lines 1063-1090)
   - Full flow: TIME → COURT → SERVICE

2. **supabase_export_20251108_221134.csv:1-25**
   - Current BAD data (all provider="Unknown")
   - Use as baseline to compare against

3. **test_provider_fix.py:1-END**
   - Local test script
   - Understand what it does before running

4. **check_supabase_data.sh:1-END**
   - Verification script
   - Shows latest Supabase records

5. **ACCEPTANCE_TEST.md**
   - Step-by-step test procedure
   - Success criteria checklist

---

## 🔄 ITERATION CYCLE

```
1. Run test_provider_fix.py
   ↓
2. Check output: "✅ TEST PASSED!" ?
   ├─ YES → Check CSV → Deploy
   └─ NO → Use Playwright MCP to debug selector
           ↓
           Fix selector
           ↓
           Go to step 1
```

**Repeat until CSV shows provider="Корт..." correctly**

---

## ⚠️ TROUBLESHOOTING

### If provider still shows "Unknown":

1. **Check selector is correct** (line 1056)
2. **Use Playwright MCP** to inspect live page:
   - Navigate to service page manually
   - Take screenshot
   - Evaluate: `document.querySelector('p.label.category-title')?.textContent`
   - Find correct selector if different

3. **Check logs** in test output:
   - Look for "⚠️ Failed to get provider: ..."
   - This shows WHY selector failed

4. **Verify you're on service page**:
   - URL should contain "select-services"
   - Page title should show court name

---

## 📊 DATA QUALITY METRICS

**Before fix**:
- Total: 23 records
- Provider="Unknown": 17 (74%)
- Provider="Не указан": 5 (22%)
- Client-ready (has both price+provider): 0 (0%)

**After fix (expected)**:
- Total: 2-5 records (new data)
- Provider="Корт...": 100%
- Client-ready: 100%

---

## 🎯 SUCCESS = CSV LOOKS CORRECT

**Only criterion that matters**: 
```csv
provider
Корт 3 (для игры 1х1)  ✅
Корт 3 (для игры 1х1)  ✅
```

**NOT**:
```csv
provider
Unknown  ❌
```

**When CSV is correct → Deploy to TimeWeb**  
**When CSV is wrong → Use Playwright MCP → Fix → Retry**

---

**END OF PLAN**
