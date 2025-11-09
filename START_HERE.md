# 🚀 START HERE - NEXT AGENT

**Last Updated**: 2025-11-02 21:00 UTC
**Status**: Code ready, needs testing during business hours

---

## 📖 READ THIS FIRST

**Main Handoff**: [`HANDOFF_FOR_NEXT_AGENT.md`](./HANDOFF_FOR_NEXT_AGENT.md)

**TL;DR:**
- ✅ Code works (captures prices: 2800₽, 5000₽, dates: 2025-11-04)
- ✅ Deduplication fixed (line 617)
- ✅ Requires date+time (line 769)
- ❌ Got 0 records: venues closed (late evening, no bookings)
- 🎯 Next: Test tomorrow 9am-6pm Moscow time

---

## 🗂️ DOCUMENTATION INDEX

**Active Documents** (use these):
1. [`HANDOFF_FOR_NEXT_AGENT.md`](./HANDOFF_FOR_NEXT_AGENT.md) - Current state & next steps
2. [`CLAUDE.md`](./CLAUDE.md) - Project overview & credentials
3. [`PROOF_OF_DATA_CAPTURE.md`](./PROOF_OF_DATA_CAPTURE.md) - How correlation works
4. [`BAD_VS_GOOD_DATA_COMPARISON.csv`](./BAD_VS_GOOD_DATA_COMPARISON.csv) - Data quality comparison

**Archived** (outdated):
- [`archive/old-handoffs-2025-11-02/`](./archive/old-handoffs-2025-11-02/) - Old session docs

---

## ⚡ QUICK START

```bash
# 1. Test during business hours (9am-6pm Moscow)
cd /Users/m/git/clients/yclents/yclients-local-fix
export SUPABASE_URL="https://zojouvfuvdgniqbmbegs.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpvam91dmZ1dmRnbmlxYm1iZWdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDMyNDgzMCwiZXhwIjoyMDc1OTAwODMwfQ.D9tQNYmStQ9EddTnxQL-N1hmmCs9CTIJgRp6qhmSJCc"
python3 test_production_code.py

# 2. If test shows good data → deploy
git push origin main

# 3. Verify after deploy
python3 export_supabase_csv.py
# Should see real prices, times, no duplicates
```

---

## 🔍 WHAT YOU NEED TO KNOW

**Problem**: Production Supabase has BAD data
- 188/200 missing times
- 200/200 fake prices ("Цена не найдена")
- 76 duplicates

**Solution**: Code fixed (lines 617, 769)
- Deduplication added
- Requires BOTH date+time
- Correlation merges 3 APIs

**Evidence**: Test run showed API capture working
```
'price_min': 2800.0  ✅ CAPTURED
'price_min': 5000.0  ✅ CAPTURED
'date': '2025-11-04' ✅ CAPTURED
```

**Why 0 results**: Late evening → no bookings available

---

## 📂 KEY FILES

**Code**:
- `src/parser/yclients_parser.py:617` - Dedup fix
- `src/parser/yclients_parser.py:769` - Requires date+time
- `src/parser/yclients_parser.py:563-630` - Correlation logic

**Tests**:
- `test_production_code.py` - Use EXACT production code
- `export_supabase_csv.py` - Export current data

**Results**:
- `SUPABASE_EXPORT.csv` - Current bad data (for comparison)
- `MULTI_URL_TEST_RESULTS.csv` - Test results (1 record, incomplete)

---

## ⚠️ IMPORTANT

**Don't read archived docs** - they're outdated and will confuse you

**Use git log** for history:
```bash
git log --oneline -10
git show d57b2cd  # Line 754 + dedup fix
```

**Credentials updated** 2025-11-02:
- Old URL (deleted): `tfvgbcqjftirclxwqwnr.supabase.co`
- New URL: `zojouvfuvdgniqbmbegs.supabase.co`

---

**Ready? Read**: [`HANDOFF_FOR_NEXT_AGENT.md`](./HANDOFF_FOR_NEXT_AGENT.md)
