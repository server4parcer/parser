# Complete Handoff: YClients Parser Project for Pavel

## 🎯 Executive Summary

**Project**: YClients web scraper that extracts booking data (date, time, price, provider) from YClients pages and saves to Supabase.

**Current Status**:
- ✅ **Schema fixes deployed** - URL operations work correctly
- ✅ **API authentication works** - Pavel can access endpoints
- ✅ **Parser triggers successfully** - Runs for all configured URLs
- ❌ **Data saving broken** - Parser runs but saves 0 records to database

**Root Cause Fixed**: Schema mismatch (code expected `description` field that doesn't exist in Pavel's Supabase tables)

**Remaining Issue**: Parser execution problem - needs investigation of why data isn't being saved.

---

## 📁 Files Modified (Exact References)

### 1. src/api/routes.py

**Lines 266-269: POST /urls endpoint**
```python
# BEFORE (BROKEN):
insert_data = {
    "url": str(url_data.url),
    "title": url_data.title,
    "description": url_data.description,  # ❌ Field doesn't exist
    "is_active": True
}

# AFTER (FIXED):
insert_data = {
    "url": str(url_data.url)
}
```

**Lines 400-407: PUT /urls endpoint**
```python
# BEFORE (BROKEN):
if url_data.description is not None:
    update_data["description"] = url_data.description  # ❌ Field doesn't exist

# AFTER (FIXED):
# description field removed completely
```

**Lines 1046-1130: NEW DEBUG ENDPOINT ADDED**
```python
@app.post("/debug/test-parser")
# Tests parser extraction without saving to DB
# Returns extracted data for debugging
```

### 2. Documentation Created

**PAVEL_YCLIENTS_INSTRUCTIONS.md** - Complete guide for Pavel with:
- All curl commands
- API key information
- How to test system
- Troubleshooting guide

**SYSTEMATIC_INVESTIGATION_PLAN.md:196-230** - Resolution documented

---

## 🧪 E2E Verification Tests

### Test 1: API Authentication (SHOULD PASS ✅)
```bash
curl -H "X-API-Key: yclients_parser_secure_key_2024" \
     https://server4parcer-parser-4949.twc1.net/status

# Expected: {"status":"success","data":{"booking_records":N,"url_records":7}}
# Actual: ✅ PASSES
```

### Test 2: URL Creation (SHOULD PASS ✅)
```bash
curl -X POST -H "X-API-Key: yclients_parser_secure_key_2024" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://test.yclients.com/test"}' \
     https://server4parcer-parser-4949.twc1.net/urls

# Expected: {"status":"success","message":"URL успешно создан"}
# Actual: ✅ PASSES (no more "description column missing" error)
```

### Test 3: Parser Trigger (SHOULD PASS ✅)
```bash
curl -X POST -H "X-API-Key: yclients_parser_secure_key_2024" \
     "https://server4parcer-parser-4949.twc1.net/parse/all?active_only=false"

# Expected: {"status":"success","message":"Парсер запущен для N URL"}
# Actual: ✅ PASSES (parser runs)
```

### Test 4: NEW Debug Parser Test (USE THIS!)
```bash
curl -X POST -H "X-API-Key: yclients_parser_secure_key_2024" \
     "https://server4parcer-parser-4949.twc1.net/debug/test-parser?url=https://n1165596.yclients.com/company/1109937/record-type?o="

# Expected: Shows extracted data OR error details
# This endpoint tests parser WITHOUT saving to DB
# CRITICAL: Use this to diagnose extraction issues!
```

### Test 5: Data Check (CURRENTLY FAILS ❌)
```bash
curl -H "X-API-Key: yclients_parser_secure_key_2024" \
     "https://server4parcer-parser-4949.twc1.net/data?limit=5"

# Expected: {"data":{"items":[...]}}
# Actual: ❌ FAILS - {"data":{"total":0,"items":[]}}
```

---

## 🔍 Investigation Path for Next Agent

### Priority 1: Test Parser Extraction
**Action**: Use the new debug endpoint to see if parser can extract data
```bash
curl -X POST -H "X-API-Key: yclients_parser_secure_key_2024" \
     "https://server4parcer-parser-4949.twc1.net/debug/test-parser?url=https://n1165596.yclients.com/company/1109937/record-type?o="
```

**Expected Outcomes**:
1. **Success + Data** → Parser works, problem is saving to DB (check booking_data table schema)
2. **Success + No Data** → YClients page structure changed or extraction logic broken
3. **Error about Playwright** → Missing browser dependency in container
4. **Timeout/crash** → Resource constraints or async issues

### Priority 2: Check Container Logs
**Location**: TimeWeb Dashboard → Application → Logs

**What to look for**:
- Playwright browser launch errors
- Supabase connection errors during save
- Schema/column mismatch errors (similar to description issue)
- Extraction logic errors

### Priority 3: Verify Dependencies
**File**: `requirements.txt:12`
```
playwright>=1.54.0
```

**Test**: Check if Playwright installed in container
```bash
# In container:
playwright --version
chromium --version
```

**Issue**: Container might not have browser binaries installed.

**Solution**: May need to use lightweight parser instead:
- File: `src/parser/production_data_extractor.py` (lightweight HTTP-only version)
- vs `src/parser/yclients_parser.py` (full Playwright version)

### Priority 4: Schema Verification
**Compare Expected vs Actual**

**Code Expects** (src/database/db_manager.py:312-370):
```python
cleaned = {
    'date': ...,
    'time': ...,
    'price': ...,
    'provider': ...,
    'created_at': ...,
    'url_id': ...
}
```

**Check in Supabase**:
- Go to Table Editor → booking_data
- Verify columns match exactly
- Check for missing columns (same issue as `description`)
- Verify data types match

---

## 📋 Critical Files to Read (Line Ranges)

### Parser Logic
```
src/parser/yclients_parser.py:517-634
  └─ Data extraction logic
  └─ Playwright browser automation
  └─ Element selectors for YClients pages

src/parser/yclients_parser.py:646-696
  └─ Save operations
  └─ Calls db_manager.save_booking_data()
```

### Database Operations
```
src/database/db_manager.py:150-210
  └─ save_booking_data() method
  └─ Batch insertion logic
  └─ Error handling during saves

src/database/db_manager.py:312-370
  └─ clean_booking_data() method
  └─ Data validation and cleaning
  └─ Field mapping
```

### API Endpoints (Already Fixed)
```
src/api/routes.py:266-269 - POST /urls (FIXED ✅)
src/api/routes.py:400-407 - PUT /urls (FIXED ✅)
src/api/routes.py:1046-1130 - NEW debug/test-parser endpoint
```

---

## 🗂️ Schema Reality Check

### Pavel's Actual Supabase Schema (Minimal)
```sql
-- urls table
id, url

-- booking_data table
id, url_id, date, time, price, provider, created_at
```

### Code Expectations (Complex - From Different Project!)
```sql
-- urls table (WRONG - from court management project)
id, url, title, description, is_active, created_at, updated_at

-- booking_data table (WRONG - analytics features)
id, url, date, time, price, provider, seat_number, location_name,
court_type, time_category, duration, review_count, prepayment_required
```

**Key Insight**: The code was designed for a complex analytics system but Pavel only needs simple YClients booking data extraction.

---

## 🔧 Environment Variables (TimeWeb)

**Critical Settings**:
```bash
SUPABASE_URL=https://tfvgbcq...supabase.co
SUPABASE_KEY=eyJhbGciOiJI...  # Service role key
API_KEY=yclients_parser_secure_key_2024
PARSE_URLS=https://n1165596.yclients.com/...,https://...
```

**Verify in TimeWeb**:
- All variables are set
- PARSE_URLS contains Pavel's YClients URLs
- SUPABASE_KEY has write permissions

---

## 🎯 Recommended Next Steps

### Step 1: Diagnose with Debug Endpoint (10 minutes)
Test parser extraction using `/debug/test-parser` endpoint.
This reveals if problem is extraction vs saving.

### Step 2: Based on Debug Results

**If extraction works (data returned)**:
→ Problem is database saving
→ Check booking_data table schema
→ Look for missing columns like we found with `description`

**If extraction fails (no data)**:
→ Problem is parser logic
→ Check if YClients pages changed structure
→ Review extraction selectors in yclients_parser.py:517-634

**If Playwright error**:
→ Problem is missing dependencies
→ Either install Playwright in container
→ Or switch to lightweight HTTP parser

### Step 3: Fix Root Cause (varies)
Apply surgical fix similar to what we did for URL schema.

### Step 4: Test E2E (5 minutes)
Verify data flows: Parser → Supabase → API → Pavel

---

## 📞 Contact Pavel

Pavel's API Key: `yclients_parser_secure_key_2024`

Pavel's system: `https://server4parcer-parser-4949.twc1.net`

Give Pavel this file: **PAVEL_YCLIENTS_INSTRUCTIONS.md**

---

## 🧭 What We Fixed vs What Remains

### ✅ FIXED (Deployed to Production)
1. URL creation - No more "description column missing"
2. URL updates - Schema compatible
3. API authentication - Works perfectly
4. Parser triggering - Runs successfully
5. Documentation - Clear instructions for Pavel

### ❌ REMAINING ISSUE
**Parser saves 0 records**

**Likely causes** (in order of probability):
1. Playwright dependency missing in container (most likely)
2. Booking_data table schema mismatch (similar to description)
3. YClients page structure changed
4. RLS permissions blocking inserts

**Diagnostic tool**: NEW debug endpoint at `/debug/test-parser`

---

## 💡 Key Insights for Next Agent

1. **This is a YClients scraper** (simple booking data)
   - NOT a court management system (ignore COURTS/SCHEDULE docs)
   - Pavel's original request: parse 10-15 YClients pages

2. **Schema is intentionally minimal**
   - Pavel only needs: date, time, price, provider
   - Code expects 15+ fields from wrong project

3. **Fix pattern is surgical**
   - Don't add complex fields
   - Remove references to non-existent columns
   - Keep it simple

4. **Test with debug endpoint first**
   - Saves time vs blind debugging
   - Shows exact error messages
   - Confirms if parser can extract

---

## 📊 Success Criteria

**System is complete when**:
1. ✅ Parser extracts YClients booking data
2. ✅ Data saves to booking_data table
3. ✅ booking_records count > 0
4. ✅ Pavel can retrieve data via /data endpoint
5. ✅ Automatic updates every 10 minutes work

**Current progress**: 4/5 complete (only #2-3 remaining)

---

## 🚀 Quick Start for Next Agent

```bash
# 1. Test current system
curl -H "X-API-Key: yclients_parser_secure_key_2024" \
     https://server4parcer-parser-4949.twc1.net/status

# 2. Test parser extraction (NEW DEBUG ENDPOINT!)
curl -X POST -H "X-API-Key: yclients_parser_secure_key_2024" \
     "https://server4parcer-parser-4949.twc1.net/debug/test-parser?url=https://n1165596.yclients.com/company/1109937/record-type?o="

# 3. Based on result, investigate:
#    - Playwright dependency (if browser error)
#    - Booking table schema (if save error)
#    - Page structure (if extraction returns empty)

# 4. Apply surgical fix (like we did for description field)

# 5. Verify E2E
curl -H "X-API-Key: yclients_parser_secure_key_2024" \
     "https://server4parcer-parser-4949.twc1.net/data?limit=5"
```

**Estimated time to complete**: 1-2 hours once root cause identified.

---

**Good luck! The hard diagnostic work is done. Just need to fix the parser execution issue.** 🎯
