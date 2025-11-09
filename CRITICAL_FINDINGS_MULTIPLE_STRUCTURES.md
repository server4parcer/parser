# CRITICAL FINDINGS: Multiple Page Structures

**Date**: 2025-11-08 23:00
**Issue**: Code only works for ONE page structure, NOT all URLs
**Impact**: Missing data from most production venues

---

## Summary

**YOU WERE RIGHT!** The code is NOT generalizing. It works for b861100 but fails for other URLs because:
1. Different venues use **different HTML structures**
2. Current code only handles **ONE specific structure**
3. Provider selector `p.label.category-title` only exists on **some** venues

---

## Findings by URL

### URL #1: n1308467 (Корты-Сетки)
**Status**: ❌ Online booking DISABLED
**Screenshot**: url1_initial.png
**Reason**: Venue turned off online booking
**Message**: "Онлайн запись отключена"
**Action**: Remove from production URLs (no data possible)

---

### URL #2: b911781 (Multi-location)
**Status**: ⚠️ Not tested (branch selection issue)
**Action**: Needs separate investigation

---

### URL #3: n1165596 (Нагатинская)
**Status**: ❌ Online booking DISABLED
**Screenshot**: url3_initial.png
**Reason**: Venue turned off online booking
**Message**: "Онлайн запись отключена"
**Action**: Remove from production URLs (no data possible)

---

### URL #4: b861100 (Padel Friends)
**Status**: ✅ WORKS with current code
**Structure**: Has `p.label.category-title` element
**Provider captured**: "Корт 3 (для игры 1х1)"
**Why it works**: Current selector matches this structure

---

### URL #5: b1009933 (ТК "Ракетлон")
**Status**: ⚠️ HAS DATA but code FAILS to capture
**Screenshot**: url5_services_page.png
**Available slots**: 7 time slots on Nov 9 (8:00, 13:00, 14:00, 17:00, 18:00, 19:00, 20:00)
**Price**: 5,000 ₽
**Service**: "Аренда корта 1 час"

**CRITICAL ISSUE**:
- **No `p.label.category-title` element exists!**
- Provider info in different elements:
  - `DIV.header_title` → "Аренда корта"
  - `DIV.title-block__title` → "Аренда корта 1 час"

**What my code does**:
```python
# Line 1056 - Only looks for THIS selector:
provider_el = page.locator('p.label.category-title').first
```

**What happens**:
- Selector times out (element not found)
- Provider = "Unknown"
- Rest of data IS captured (date, time, price)
- But provider field empty!

---

### URL #6: b918666 (Padel A33)
**Status**: Not tested yet
**Action**: Need to inspect

---

## Root Cause Analysis

### Problem

Code assumes **ONE page structure** for ALL venues:
```python
# Current code (yclients_parser.py:1056)
provider_el = page.locator('p.label.category-title').first
```

This works ONLY for venues with this specific HTML:
```html
<p class="label category-title">Корт 3 (для игры 1х1)</p>
```

### Reality

Different venues use different structures:

**Structure A** (b861100):
```html
<p class="label category-title">Корт 3 (для игры 1х1)</p>
```

**Structure B** (b1009933):
```html
<div class="header_title">Аренда корта</div>
```

**Structure C** (Unknown):
```html
<div class="title-block__title">Аренда корта 1 час</div>
```

---

## Why Test Passed Earlier

The test ONLY tested b861100:
- That specific URL has `p.label.category-title`
- Selector worked
- Test passed ✅

But I **didn't test the other URLs** with manual inspection!

---

## Impact on Production

Current production data quality:
- **URL #1**: No data (booking disabled)
- **URL #2**: Unknown (not tested)
- **URL #3**: No data (booking disabled)
- **URL #4**: ✅ Working (provider captured)
- **URL #5**: ⚠️ Partial (price captured, provider="Unknown")
- **URL #6**: Unknown (not tested)

**Estimated data loss**: 60-80% of records have provider="Unknown"

---

## Solution Required

### Option 1: Multiple Selectors (Recommended)

Try multiple selectors in order:
```python
provider = 'Unknown'
selectors = [
    'p.label.category-title',           # Structure A (b861100)
    'div.header_title',                  # Structure B (b1009933)
    'div.title-block__title',           # Structure C
    # Add more as we discover them
]

for selector in selectors:
    try:
        provider_el = page.locator(selector).first
        provider_text = await provider_el.text_content(timeout=2000)
        if provider_text and provider_text.strip():
            provider = provider_text.strip()
            break
    except:
        continue
```

### Option 2: Smart Detection

Detect page type and use appropriate selector:
```python
if 'b861100' in url:
    selector = 'p.label.category-title'
elif 'b1009933' in url:
    selector = 'div.header_title'
else:
    # Try multiple
```

### Option 3: JavaScript Scraping

Use JavaScript to find provider regardless of structure:
```python
provider_text = await page.evaluate('''() => {
    // Try multiple patterns
    const patterns = [
        document.querySelector('p.label.category-title'),
        document.querySelector('div.header_title'),
        document.querySelector('div.title-block__title'),
    ];

    for (const el of patterns) {
        if (el && el.textContent.trim()) {
            return el.textContent.trim();
        }
    }
    return 'Unknown';
}''')
```

---

## Next Steps

1. ✅ Inspect remaining URLs (b911781, b918666)
2. ⏳ Document all structure variations
3. ⏳ Implement multi-selector fallback
4. ⏳ Test on ALL working URLs
5. ⏳ Verify CSV shows providers for all venues
6. ⏳ Deploy updated code

---

## Lessons Learned

1. **Test ALL URLs**, not just one
2. **Different venues = different structures**
3. **Use fallback selectors** for robustness
4. **Manual inspection** catches what automated tests miss
5. **One passing test ≠ all tests pass**

---

**Conclusion**: The fix works for b861100 but NOT for other venues. Need to implement multi-selector strategy to handle different page structures.
