# 🚀 START HERE - Next Agent

**READ THIS FILE FIRST**: `/Users/m/git/clients/yclents/yclients-local-fix/START_HERE_NEXT_AGENT.md`

---

## 📖 WHAT TO READ (In Order)

### 1️⃣ **This File** - Overview (you are here)
```
/Users/m/git/clients/yclents/yclients-local-fix/START_HERE_NEXT_AGENT.md
```

### 2️⃣ **Complete Execution Plan** - Full instructions
```
/Users/m/git/clients/yclents/yclents-local-fix/COMPLETE_PLAN_FOR_NEXT_AGENT.md
```
- 📋 4-phase execution plan
- 📁 Exact file paths and line numbers
- ✅ Acceptance criteria checklist
- 🎭 When/how to use Playwright MCP

### 3️⃣ **Current Bad CSV** - See the problem
```
/Users/m/git/clients/yclents/yclients-local-fix/supabase_export_20251108_221134.csv
```
Lines 1-25: All have provider="Unknown" ❌

### 4️⃣ **Parser Code** - Where the bug is
```
/Users/m/git/clients/yclents/yclients-local-fix/src/parser/yclients_parser.py
```
Lines 1050-1097: Provider scraping logic (line 1056 is critical)

### 5️⃣ **Test Script** - Run this locally
```
/Users/m/git/clients/yclents/yclients-local-fix/test_provider_fix.py
```
Full file: Automated test that saves to Supabase

---

## 🎯 QUICK SUMMARY

**Problem**: CSV shows `provider="Unknown"` instead of `"Корт 3 (для игры 1х1)"`

**Root Cause**: Wrong selector in `src/parser/yclients_parser.py:1056`

**Fix**: Already applied - selector changed to `p.label.category-title`

**Your Job**: 
1. Clear Supabase
2. Run test locally
3. Verify CSV shows correct provider
4. Deploy to TimeWeb ONLY if CSV is correct

---

## 🏗️ PROJECT STRUCTURE

```
/Users/m/git/clients/yclents/yclients-local-fix/
│
├── START_HERE_NEXT_AGENT.md          ← YOU ARE HERE
├── COMPLETE_PLAN_FOR_NEXT_AGENT.md   ← READ NEXT (full plan)
├── ACCEPTANCE_TEST.md                 ← Test procedure
│
├── src/parser/
│   └── yclients_parser.py            ← LINE 1056: The fix
│
├── test_provider_fix.py              ← RUN THIS (local test)
├── clear_supabase.sh                 ← Step 1: Clear old data
├── check_supabase_data.sh            ← Step 3: Verify results
│
├── supabase_export_20251108_221134.csv  ← Current BAD data
└── venv/                             ← Python virtual environment
```

---

## 🔑 CRITICAL INFORMATION

### Supabase Credentials (Already in Scripts)
```
URL: https://zojouvfuvdgniqbmbegs.supabase.co
KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpvam91dmZ1dmRnbmlxYm1iZWdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDMyNDgzMCwiZXhwIjoyMDc1OTAwODMwfQ.D9tQNYmStQ9EddTnxQL-N1hmmCs9CTIJgRp6qhmSJCc
Table: booking_data
```

### Test URL
```
https://b861100.yclients.com/company/804153/personal/select-time?o=m-1
```

### Python Environment
```bash
# Virtual environment already exists
/Users/m/git/clients/yclents/yclients-local-fix/venv/bin/python3
```

---

## ⚡ QUICK START (3 Commands)

```bash
cd /Users/m/git/clients/yclents/yclients-local-fix

# 1. Clear old data
./clear_supabase.sh

# 2. Run test (saves to Supabase automatically)
venv/bin/python3 test_provider_fix.py

# 3. Check results
./check_supabase_data.sh
```

**Expected**: Provider shows "Корт 3 (для игры 1х1)" instead of "Unknown"

---

## 📚 WHAT YOU NEED TO KNOW

### 1. **The User Flow (Playwright Automation)**

The parser automates this user journey:

```
1. Load page: select-time?o=m-1
   ↓
2. Click: "Перейти к ближайшей дате" (Go to nearest date button)
   ↓
3. Select: Time slot (e.g., 9:00)
   ↓
4. Click: "Продолжить" (Continue button)
   ↓
5. Land on: select-services page  ← THIS IS WHERE WE SCRAPE
   ↓
6. Extract: provider from <p class="label category-title">Корт 3...</p>
```

### 2. **Why It Was Broken**

**Old selector** (line 1056):
```python
provider_el = page.locator('paragraph').first  # ← Wrong! Times out
```

**New selector** (line 1056):
```python
provider_el = page.locator('p.label.category-title').first  # ← Correct!
```

The actual HTML element is:
```html
<p class="label category-title">Корт 3 (для игры 1х1)</p>
```

### 3. **How to Verify the Fix**

**Good data looks like**:
```csv
id,date,time,price,provider
36285,2025-11-10,09:00:00,1 200 ₽,Корт 3 (для игры 1х1)  ✅
```

**Bad data looks like**:
```csv
id,date,time,price,provider
36260,2025-11-10,09:00:00,1 200 ₽,Unknown  ❌
```

### 4. **When to Use Playwright MCP**

**Use it ONLY if**:
- Test fails (provider still shows "Unknown")
- Need to debug selector on live page
- Page structure changed

**How to use**:
1. Navigate: `mcp__playwright__browser_navigate(url="...")`
2. Take screenshot: `mcp__playwright__browser_take_screenshot(...)`
3. Inspect: `mcp__playwright__browser_evaluate(function="...")`
4. Find correct selector
5. Update line 1056
6. Re-test

**Don't use it if**:
- Test passes ✅
- CSV looks correct ✅

### 5. **Deployment to TimeWeb**

**ONLY deploy after**:
- ✅ Local test passes
- ✅ CSV shows provider="Корт..."
- ✅ All acceptance criteria met

**How to deploy**:
```bash
git add src/parser/yclients_parser.py
git commit -m "Fix: Capture court names in provider field"
git push origin main
```

TimeWeb will auto-detect and deploy in ~20 minutes.

---

## 🎭 PLAYWRIGHT MCP USAGE (If Needed)

### Scenario 1: Test Still Fails

If `test_provider_fix.py` shows provider="Unknown":

**Step 1**: Navigate to service page
```python
mcp__playwright__browser_navigate(
    url="https://b861100.yclients.com/company/804153/personal/select-services?o=m-1d2509110900"
)
```

**Step 2**: Take screenshot
```python
mcp__playwright__browser_take_screenshot(filename="service_page.png")
```

**Step 3**: Inspect for provider element
```python
mcp__playwright__browser_evaluate(function='''() => {
    // Find all paragraph elements
    const allP = document.querySelectorAll('p');
    const results = [];
    allP.forEach(p => {
        if (p.textContent.includes('Корт')) {
            results.push({
                tag: p.tagName,
                class: p.className,
                text: p.textContent.trim()
            });
        }
    });
    return results;
}''')
```

**Step 4**: Use correct selector found

**Step 5**: Update line 1056 with new selector

**Step 6**: Re-run `test_provider_fix.py`

### Scenario 2: Different Court Name

If you see different text (not "Корт 3"), that's OK!
- "Корт 1 (для игры 1х1)" ✅
- "Корт 2 (для игры 2х2)" ✅
- Any text with "Корт" ✅

As long as it's NOT "Unknown" ❌

---

## 📊 ACCEPTANCE CRITERIA (Checklist)

Before you deploy, verify ALL of these:

```
Phase 1: Code Check
- [ ] Line 1056 has 'p.label.category-title' selector
- [ ] No syntax errors in yclients_parser.py

Phase 2: Clear Data
- [ ] clear_supabase.sh runs successfully
- [ ] Supabase shows 0 records

Phase 3: Local Test
- [ ] test_provider_fix.py runs without errors
- [ ] Output shows "✅ TEST PASSED!"
- [ ] Provider field contains "Корт" text
- [ ] Test saves records to Supabase

Phase 4: Verify CSV
- [ ] check_supabase_data.sh shows new records
- [ ] Provider column has "Корт..." NOT "Unknown"
- [ ] Price column populated (e.g., "1,200 ₽")
- [ ] Date is future date (e.g., 2025-11-10)
- [ ] CSV export file created successfully

Deployment Ready
- [ ] ALL above criteria pass
- [ ] CSV looks correct (most important!)
- [ ] Ready to git push
```

---

## ⚠️ COMMON PITFALLS

### ❌ Don't:
- Deploy before testing locally
- Skip clearing Supabase (old data will confuse you)
- Ignore test failures
- Use Playwright MCP for routine testing (use test script instead)
- Deploy if CSV still shows "Unknown"

### ✅ Do:
- Read COMPLETE_PLAN_FOR_NEXT_AGENT.md fully
- Clear Supabase before testing
- Run test_provider_fix.py and check output
- Verify CSV shows correct data
- Use Playwright MCP only for debugging
- Deploy only after CSV is correct

---

## 🆘 IF YOU GET STUCK

### Provider still shows "Unknown":

1. **Check selector** in line 1056
   ```bash
   grep -n "p.label.category-title" src/parser/yclients_parser.py
   ```
   Should return line 1056

2. **Check test output** for error messages
   Look for: "⚠️ Failed to get provider: ..."

3. **Use Playwright MCP** to inspect live page
   Take screenshot of service page
   Find correct selector

4. **Read the full plan**:
   ```
   /Users/m/git/clients/yclents/yclents-local-fix/COMPLETE_PLAN_FOR_NEXT_AGENT.md
   ```

---

## 📞 HANDOFF CONTEXT

### What Previous Agent Did:
1. ✅ Identified issue: provider="Unknown" in CSV
2. ✅ Used Playwright MCP to inspect service page
3. ✅ Found correct selector: `p.label.category-title`
4. ✅ Applied fix to line 1056
5. ✅ Committed code to GitHub
6. ⏸️ **Did NOT test locally yet** ← Your job starts here

### What You Need to Do:
1. Test the fix locally
2. Verify CSV shows correct data
3. Deploy ONLY if CSV is correct

### Files Already Created:
- ✅ test_provider_fix.py (test script)
- ✅ clear_supabase.sh (clear data script)
- ✅ check_supabase_data.sh (verify script)
- ✅ COMPLETE_PLAN_FOR_NEXT_AGENT.md (full instructions)
- ✅ ACCEPTANCE_TEST.md (test procedure)

### Git Status:
```
Branch: main
Last commit: 562b305 "Fix: Capture court names in provider field"
Files changed: src/parser/yclients_parser.py (1 line)
Ready to test: YES
Ready to deploy: NO (test first!)
```

---

## 🎯 YOUR GOAL

**Get this CSV**:
```csv
provider
Корт 3 (для игры 1х1)
```

**NOT this CSV**:
```csv
provider
Unknown
```

**When CSV is correct → Deploy to TimeWeb**

---

## 🚦 DECISION TREE

```
Start
  ↓
Read COMPLETE_PLAN_FOR_NEXT_AGENT.md
  ↓
Clear Supabase (./clear_supabase.sh)
  ↓
Run test (venv/bin/python3 test_provider_fix.py)
  ↓
Check output: "✅ TEST PASSED!" ?
  ├─ YES → Check CSV (./check_supabase_data.sh)
  │         ↓
  │        Provider = "Корт..." ?
  │         ├─ YES → Deploy! (git push)
  │         └─ NO → Debug with Playwright MCP
  │
  └─ NO → Debug with Playwright MCP
            ↓
           Fix selector (line 1056)
            ↓
           Re-run test
```

---

## 📋 NEXT STEPS

1. Read `/Users/m/git/clients/yclents/yclients-local-fix/COMPLETE_PLAN_FOR_NEXT_AGENT.md`
2. Follow the 4-phase plan
3. Verify CSV looks correct
4. Deploy when ready

**Good luck! The fix is already in place, you just need to verify it works.**

---

**END OF START HERE**
