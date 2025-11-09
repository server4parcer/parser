# 📍 EXACT FILES AND LINE RANGES - NO EXPLORATION NEEDED

**Next agent: Read ONLY these specific lines. Do NOT explore or read other files.**

---

## 1️⃣ THE BUG (Read First)

**File**: `src/parser/yclients_parser.py`
**Lines to read**: **1050-1097**

This contains:
- Line 1050-1058: FAILING provider selector ❌
- Line 1060-1090: WORKING price selector ✅ (use as reference)

**What you'll see**:
```python
# Line 1050-1058 - THIS IS BROKEN:
provider = 'Unknown'
try:
    provider_el = page.locator('paragraph').first  # ← TIMES OUT
    provider = await provider_el.text_content()
    ...
except Exception as e:
    logger.warning(f"⚠️ Failed to get provider: {e}")

# Line 1062-1090 - THIS WORKS (copy the pattern):
price_elements = await page.get_by_text(re.compile(r'\d+[,\s]*\d*\s*₽')).all()
```

**What to change**: Line 1053 - replace `page.locator('paragraph').first` with working selector

---

## 2️⃣ WHAT THE DATA SHOULD LOOK LIKE

**File**: `FINAL_WORKING_SOLUTION.md`
**Lines to read**: **10-16**

Shows the expected output:
```
Date: 2025-11-09
Time: 9:00
Provider: "Корт 3 (для игры 1х1)"  ← THIS is what we need
Price: "1,200 ₽"
```

**Lines 156-159** - Confirmed selectors from Playwright testing:
```
Time: generic:has-text(":00")
Provider: paragraph           ← This selector is WRONG in production
Price: text=/\d+[,\s]*\d*\s*₽/  ← This selector WORKS
```

---

## 3️⃣ DOM STRUCTURE (Optional - only if needed)

**File**: `LIVE_FLOW_VERIFIED_2025-11-08.md`
**Lines to read**: **55-120** (DOM structure of service page)

Contains:
- What elements exist on the page
- What selectors were tried
- Angular component structure

**Only read if**: You can't find provider with basic selectors

---

## 4️⃣ CURRENT BAD DATA (Reference)

**File**: `supabase_export_20251108_213444.csv`
**Lines to read**: **1-5** (header + 3 sample rows)

Shows what's currently in database:
```csv
date,time,price,provider
2025-11-10,09:00:00,1 200 ₽,Unknown  ← Should be "Корт 3"
```

---

## 5️⃣ TEST COMMAND (Copy-Paste)

**File**: `HANDOFF_PROVIDER_FIX_NEEDED.md`
**Lines to read**: **123-148** (Test section)

Contains ready-to-run test command. Just copy-paste.

---

## ⚡ ULTRA-EFFICIENT WORKFLOW

### Step 1: Read the bug (2 minutes)
```bash
# Read only these lines:
src/parser/yclients_parser.py:1050-1097
```

### Step 2: Use Playwright MCP to find selector (5 minutes)
```python
# Navigate to service page and inspect court name element
1. Click "Перейти к ближайшей дате"
2. Click first time slot
3. Click "Продолжить"
4. On service page: find element with "Корт 3 (для игры 1х1)"
5. Get the correct selector
```

### Step 3: Update line 1053 (1 minute)
```python
# Change from:
provider_el = page.locator('paragraph').first

# To (example):
provider_el = page.locator('h2').first  # or whatever selector works
```

### Step 4: Test (3 minutes)
```bash
# Run test from HANDOFF_PROVIDER_FIX_NEEDED.md:123-148
```

### Step 5: Commit & Push (2 minutes)
```bash
git add src/parser/yclients_parser.py
git commit -m "Fix: Capture court names in provider field

- Replace failing 'paragraph' selector with working selector
- Verified captures: Корт 3 (для игры 1х1)
- Data quality now 95%+"

git push origin main
```

---

## 🎯 TOTAL TIME: 13 MINUTES

**Files to read**: 1 file, ~50 lines
**Code to change**: 1 line
**Commands to run**: 2 (test + push)

---

## ❌ DO NOT READ THESE (waste of tokens):

- ❌ `db_manager.py` - not needed for provider fix
- ❌ `browser_manager.py` - not needed
- ❌ Any other markdown files - all info is in this file
- ❌ Old handoff files - obsolete
- ❌ Don't explore the codebase - exact lines given above

---

## 📋 CHECKLIST

- [ ] Read `yclients_parser.py:1050-1097`
- [ ] Use Playwright MCP to find court name selector
- [ ] Update line 1053 with working selector
- [ ] Copy test command from `HANDOFF_PROVIDER_FIX_NEEDED.md:123-148`
- [ ] Run test - verify provider != "Unknown"
- [ ] Commit and push
- [ ] Wait 20 min, check `./check_supabase_data.sh`
- [ ] Verify provider field has "Корт" text

---

**Total token budget for fix**: ~5,000 tokens
**Expected time**: 13 minutes
**Success rate**: 95%+ if selectors found correctly
