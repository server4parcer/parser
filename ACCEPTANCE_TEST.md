# 🧪 ACCEPTANCE TEST - Provider Field Fix

**Goal**: Verify that provider field captures "Корт 3 (для игры 1х1)" instead of "Unknown"

---

## ✅ Expected Result

After running the test, Supabase should contain records with:
- **provider**: "Корт 3 (для игры 1х1)" ✅ (NOT "Unknown")
- **price**: "1,200 ₽" or similar ✅
- **date**: Future date (e.g., 2025-11-10) ✅
- **time**: Time slot (e.g., 09:00:00) ✅

---

## 🚀 Run Acceptance Test

```bash
cd /Users/m/git/clients/yclents/yclients-local-fix

# Step 1: Clear Supabase data
./clear_supabase.sh

# Step 2: Run parser locally (saves to Supabase)
./run_local_test.sh

# Step 3: Verify data in Supabase
./check_supabase_data.sh
```

---

## 📋 Step-by-Step Commands

### Step 1: Clear Supabase
```bash
./clear_supabase.sh
```
Expected output:
```
Clearing all data from Supabase booking_data table...
✅ Deleted X records
✅ Table is now empty
```

### Step 2: Run Local Test
```bash
./run_local_test.sh
```
Expected output:
```
TESTING PROVIDER FIELD CAPTURE - LOCAL RUN
...
✅ TEST PASSED!
   Provider captured correctly: 'Корт 3 (для игры 1х1)'
   Price captured: 1,200 ₽
...
✅ Saved N records to Supabase
```

### Step 3: Check Supabase Data
```bash
./check_supabase_data.sh
```
Expected output:
```
Latest 20 records:

1. ID: XXXXX
   Date: 2025-11-10 | Time: 09:00:00
   Price: 1,200 ₽ | Provider: Корт 3 (для игры 1х1)  ← ✅ THIS!
   Created: 2025-11-08...
```

---

## ❌ Failure Indicators

If you see:
```
Provider: Unknown  ← ❌ BAD
```

Then the fix didn't work. Check:
1. Is line 1056 in `src/parser/yclients_parser.py` using `p.label.category-title`?
2. Are there any errors in the test output?

---

## 🎯 Success Criteria

- [ ] Supabase clears successfully
- [ ] Local test runs without errors
- [ ] Test output shows "✅ TEST PASSED!"
- [ ] Provider field contains "Корт" text
- [ ] check_supabase_data.sh shows provider != "Unknown"
- [ ] At least 1 record with valid price + provider

---

**When all criteria pass, the fix is ready to deploy to TimeWeb.**
