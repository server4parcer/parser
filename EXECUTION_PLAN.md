# Execution Plan - Complete YClients Parser Fix

## Current Status

**Commits made:**
- 37ad54c: Fixed critical logic bugs (date AND time requirement, DOM+API merge)

**Code changes:**
1. `src/parser/yclients_parser.py` line 1422: `or` → `and`
2. `src/parser/yclients_parser.py` lines 796-815: Added merge logic

**Known issues:**
- Local testing blocked by disk space
- Merge logic is basic (may create duplicates)
- Need to verify navigation triggers timeslots API

## Deployment Steps

### Step 1: Push to GitHub

```bash
cd /Users/m/git/clients/yclents/yclients-local-fix
git push origin main
```

This triggers TimeWeb auto-deployment from oneaiguru/yclients-parser.

### Step 2: Verify Deployment

**Check TimeWeb logs:**
- Log into TimeWeb dashboard
- Check container logs for "🔧 FIX: Critical logic bugs" commit
- Verify no errors during startup

**Test production endpoint:**
```bash
curl -s "https://server4parcer-parser-4949.twc1.net/data?api_key=yclients_parser_secure_key_2024&limit=5" | python -m json.tool
```

**Expected output:**
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "date": "2025-11-04",
        "time": "14:00:00",
        "price": "2800₽",
        "provider": "Корт А33",
        "seat_number": "А33"
      }
    ]
  }
}
```

### Step 3: Trigger Parser Manually

If data is stale, force parser run:

```bash
curl -X POST "https://server4parcer-parser-4949.twc1.net/parse?url=https://n1165596.yclients.com/company/1109937/record-type?o=&api_key=yclients_parser_secure_key_2024"
```

Wait 2-3 minutes, then check `/data` endpoint again.

## Verification Checklist

- [ ] All 5 fields present in data: date, time, price, provider, seat_number
- [ ] Prices are real values (2800₽, 5000₽), not "Цена не найдена"
- [ ] Times are present (not None)
- [ ] At least 20+ records per URL
- [ ] No duplicate records

## If Issues Found

### Issue: Still getting dates-only (no time/price)

**Diagnosis:**
```bash
# Check production logs
# Look for: "⚠️ [STRATEGY] API mode has no date/time, falling back"
# Then: "🔗 [MERGE] DOM extracted X records, have Y API captures"
```

**If no merge logs:**
- Navigation might be failing
- Branch selection might not work
- Playwright might not be installed in production

**Fix:**
Read `/Users/m/git/clients/yclents/yclients-local-fix/src/parser/yclients_parser.py` lines 1021-1097 (`navigate_yclients_flow`)
- Add more logging
- Verify branch click succeeds
- Add timeslot wait/click logic

### Issue: Duplicate records

**Diagnosis:**
Merge logic (lines 803-810) is too simple - adds both DOM and API results without deduplication.

**Fix:**
```python
# Improve merge logic with deduplication by (date, time, provider):
seen = set()
for rec in merged:
    key = (rec.get('date'), rec.get('time'), rec.get('provider'))
    if key not in seen:
        final.append(rec)
        seen.add(key)
```

### Issue: Navigation timeout

**Diagnosis:**
Playwright/browser not working in TimeWeb Docker environment.

**Check:**
- Dockerfile line 22-23: Playwright installation
- Production logs: "playwright install" errors
- Container has required dependencies

**Fix:**
May need to switch to lightweight HTTP-only parser (no browser).

## Alternative: Lightweight Mode

If Playwright fails in production, use API-only mode:

**File:** `super_simple_startup.py`
- Already exists
- Uses `lightweight_parser.py` (no browser)
- Only captures what's available via HTTP

**Limitation:**
- Won't trigger timeslots API (needs clicks)
- Will only get services + dates
- Missing times/prices

## Production Credentials

**Supabase:**
- URL: https://tfvgbcqjftirclxwqwnr.supabase.co
- Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRmdmdiY3FqZnRpcmNseHdxd25yIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mjc3Nzk2NywiZXhwIjoyMDY4MzUzOTY3fQ.4szXEDqL7KhQlM3RX89DwiFpIO8LxKRek8-CkTM1-aE

**TimeWeb:**
- Production API: https://server4parcer-parser-4949.twc1.net
- API Key: yclients_parser_secure_key_2024

**GitHub:**
- Repo: https://github.com/oneaiguru/yclients-parser.git
- Auto-deploy: Push to main branch

## Files Changed This Session

1. `src/parser/yclients_parser.py` - Bug fixes (commit 37ad54c)
2. `RESEARCH_SESSION_2025-11-01.md` - This session's findings (NEW)
3. `EXECUTION_PLAN.md` - This file (NEW)
4. `CLAUDE.md` - Will update to reference new docs (TODO)

## Next Agent Instructions

1. Read RESEARCH_SESSION_2025-11-01.md for problem analysis
2. Read this file for deployment steps
3. Fix disk space issue on local Mac
4. Test locally FIRST before production deploy
5. If tests pass, push to GitHub and verify production
6. If tests fail, read navigate_yclients_flow() code and add more logging

## Success Metrics

**Before:** 28 records with date only
```
date=2025-11-04, time=None, price=None, provider=None
```

**After (target):** 50+ records with all fields
```
date=2025-11-04, time=14:00:00, price=2800₽, provider=Корт А33, seat_number=А33
```
