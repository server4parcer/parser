# ⏰ Verification Guide - Provider Field Fix

**Quick Start**: Wait 30 minutes, then run the verification command below.

---

## ⚡ Quick Verification (After 22:50 UTC)

```bash
cd /Users/m/git/clients/yclents/yclients-local-fix
./check_supabase_data.sh
```

---

## ✅ What to Look For

**SUCCESS indicators:**

1. **New record created** after `2025-11-08 13:52:04`
2. **Provider field** shows something like:
   - `Корт 3 (для игры 1х1)` ✅
   - `Корт 1 (...)` ✅
   - `Корт 2 (...)` ✅

3. **NOT showing**:
   - `Unknown` ❌
   - `Не указан` ❌

**Example of SUCCESS:**
```
ID: 36285
Date: 2025-11-10 | Time: 09:00:00
Price: 1 200 ₽ | Provider: Корт 3 (для игры 1х1)  ← ✅ THIS!
Created: 2025-11-08T14:15:23.xxxxx
```

---

## ❌ If Still Showing "Unknown"

1. Wait another 20 minutes (maybe cron hasn't run yet)
2. Check TimeWeb deployment logs
3. Read: `SESSION_COMPLETE_2025-11-08.md` → "If Fix Doesn't Work"

---

## 📊 Current Baseline (Before Fix)

```
Latest record: ID 36284
Provider: Unknown  ← All records show this
Created: 2025-11-08 13:52:04
```

**After fix**, you should see:
```
Latest record: ID 36285+
Provider: Корт 3 (для игры 1х1)  ← NEW!
Created: 2025-11-08 14:XX:XX
```

---

## 🕐 Timeline

- **22:08** - Fix pushed to GitHub
- **22:30** - TimeWeb should have deployed
- **22:50** - First new data should appear
- **23:10** - Second batch (if cron is every 20 min)

**Check any time after 22:50 UTC**

---

## 📁 Related Documents

- `FIX_SUMMARY.md` - Technical details
- `SESSION_COMPLETE_2025-11-08.md` - Full session report
- `HANDOFF_PROVIDER_FIX_NEEDED.md` - Original problem

---

## 💡 Pro Tip

Export and compare:
```bash
# Before fix (existing export):
cat supabase_export_20251108_213444.csv | grep "Unknown"

# After fix (new export):
./check_supabase_data.sh  # Creates new export
# Check the newest export file for "Корт"
```

---

**That's it!** Just wait 30 minutes and run the script. 🚀
