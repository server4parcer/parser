# 🎯 PLAYWRIGHT EXPLORATION FINDINGS - 2025-11-02

## CRITICAL DISCOVERY: ACTUAL UI FLOW IS DIFFERENT!

### ❌ What Handoff Docs Said (INCORRECT):
```
1. Select branch
2. Select service → shows price "6,500 ₽"
3. Select court → shows "Корт №1"
4. Select date/time → shows calendar
```

### ✅ What Actually Happens (CORRECT):
```
1. Select branch → IMMEDIATELY redirects to /personal/select-time (Calendar)
2. Select date (November 26) → shows time slots
3. Select time (22:00) → URL: /personal/select-time?o=d2526112200
4. Click "Продолжить" → redirects to /personal/select-master (Court Selection)
5. Select court (Корт №1) → URL: /personal/select-master?o=m3545010d2526112200
6. Click "Продолжить" → redirects to /personal/select-services (Service/Price)
7. Price page shows: "6,500 ₽", "Падел-корт, 1 час - тариф «Прайм-тайм»"
```

**ORDER: TIME → COURT → SERVICE (not SERVICE → COURT → TIME!)**

---

## 📸 Screenshots Evidence

### 1. Branch Selection Page
**URL**: `https://b911781.yclients.com/select-city/2/select-branch?o=`
**File**: `branch_selection_page.png`
**Data**: 3 locations, need to click first available

### 2. Calendar/Time Selection (FIRST STEP!)
**URL**: `https://b911781.yclients.com/company/1168982/personal/select-time?o=`
**File**: `calendar_page_direct.png`
**Data Available**:
- ✅ Dates: November 2, 3, 4, ... 30
- ✅ Time slots: "7:00", "22:00"
- ✅ Time categories: "Утро" (Morning), "Вечер" (Evening)

**APIs Called**:
```
POST /api/v1/b2c/booking/availability/search-dates
POST /api/v1/b2c/booking/availability/search-timeslots (x2)
```

### 3. Court Selection Page (SECOND STEP!)
**URL**: `https://b911781.yclients.com/company/1168982/personal/select-master?o=d2526112200`
**File**: `court_selection_with_names.png`
**Data Available**:
- ✅ Court names: "Корт №1", "Корт №3", "Корт №4", ... "Корт №10"
- ✅ Reviews: "4 отзыва" (4 reviews)
- ✅ Provider type: "Корт" (Court)
- ✅ Prepayment: "Предоплата" (Prepayment required)
- ✅ Images for each court

**APIs Called**:
```
POST /api/v1/b2c/booking/availability/search-staff
POST /api/v1/b2c/booking/availability/search-services
```

### 4. Service/Price Page (FINAL STEP!)
**URL**: `https://b911781.yclients.com/company/1168982/personal/select-services?o=m3545010d2526112200`
**File**: `service_price_page.png`
**Data Available**:
- ✅ Service name: "Падел-корт, 1 час - тариф «Прайм-тайм»"
- ✅ Duration: "1 ч" (1 hour)
- ✅ **PRICE: "6,500 ₽"** ← THE MONEY DATA!
- ✅ Prepayment: "100% предоплата"
- ✅ Category: "Падел-корты"

**APIs Called**:
```
POST /api/v1/b2c/booking/availability/search-services
POST /api/v1/b2c/booking/availability/search-dates
POST /api/v1/b2c/booking/availability/search-timeslots
```

---

## 🔑 Key API Endpoints Discovered

All APIs are POST requests to `https://platform.yclients.com/api/v1/b2c/booking/availability/`

| API Endpoint | When Called | Data Contains |
|-------------|-------------|---------------|
| `search-dates` | After branch/time page load | Available dates |
| `search-timeslots` | After date selection | Time slots with datetime |
| `search-staff` | After time selection | Court/staff info |
| `search-services` | After court selection | Service names, prices |

**All these APIs are ALREADY captured by existing code at lines 132-137!**

---

## 🛠️ What Existing Code Does

### ✅ What Works:
1. **API Capture** (`lines 100-172`): Listens for ALL API responses ✅
2. **Multi-location Handler** (`lines 257-308`): Clicks first branch ✅
3. **Page Type Detection** (`lines 218-256`): Detects which page we're on ✅
4. **API Correlation** (`lines 563-630`): Merges data from different APIs ✅

### ❌ What's Broken:
1. **`handle_time_selection_page` (`lines 370-472`)**:
   - Extracts dates and times from DOM ✅
   - BUT STOPS THERE! Doesn't continue to court selection ❌
   - Doesn't scrape date/time BEFORE clicking ❌
   - Returns static data instead of continuing flow ❌

2. **`navigate_yclients_flow` (`lines 474-550`)**:
   - Expects wrong flow order (service → court → time)
   - Should not be called for multi-location venues
   - Hardcoded for 4-step flow that doesn't match reality

---

## 🎯 THE FIX NEEDED

### Option A: Enhance `handle_time_selection_page` (RECOMMENDED)

**Current behavior** (lines 370-472):
```python
async def handle_time_selection_page(self, page, url):
    # Extract dates and times
    dates = await page.locator('.calendar-day').all()
    for date in dates[:2]:
        await date.click()
        time_slots = await page.locator('[data-time]').all()
        for slot in time_slots[:5]:
            result = {
                'date': parse_date(date_text),
                'time': time_text,
                'price': 'Доступно',  # ← NO PRICE!
                'provider': 'Не указан'  # ← NO PROVIDER!
            }
            results.append(result)
    return results  # ← STOPS HERE!
```

**NEW behavior needed**:
```python
async def handle_time_selection_page(self, page, url):
    # Extract dates and times from DOM
    dates = await page.locator('.calendar-day').all()

    scraped_data = {'dates': [], 'times': [], 'courts': [], 'services': []}

    for date in dates[:2]:
        date_text = await date.text_content()
        scraped_data['dates'].append(date_text)

        await date.click()
        await page.wait_for_timeout(1000)

        time_slots = await page.locator('[data-time]').all()
        for slot in time_slots[:3]:
            time_text = await slot.text_content()
            scraped_data['times'].append(time_text)

            # ← NEW: Click time and continue to court selection!
            await slot.click()

            # Check for "Продолжить" button
            continue_btn = page.get_by_role('button', name='Продолжить')
            if await continue_btn.is_visible():
                await continue_btn.click()
                await page.wait_for_load_state('networkidle')

                # NOW on court selection page!
                # Scrape court names BEFORE clicking
                courts = await page.locator('ui-kit-simple-cell').all()
                for court in courts[:3]:
                    court_name = await court.locator('ui-kit-headline').text_content()
                    scraped_data['courts'].append(court_name)

                    await court.click()
                    continue_btn = page.get_by_role('button', name='Продолжить')
                    if await continue_btn.is_visible():
                        await continue_btn.click()
                        await page.wait_for_load_state('networkidle')

                        # NOW on service/price page!
                        # Scrape prices from DOM
                        price_elements = await page.locator('[class*="price"]').all()
                        service_elements = await page.locator('ui-kit-headline').all()

                        for i, service in enumerate(service_elements):
                            service_name = await service.text_content()
                            price = await price_elements[i].text_content() if i < len(price_elements) else None

                            scraped_data['services'].append({
                                'name': service_name,
                                'price': price,
                                'court': court_name,
                                'date': date_text,
                                'time': time_text
                            })

                        # Go back to court selection
                        await page.go_back()
                        await page.wait_for_timeout(1000)

                # Go back to time selection
                await page.go_back()
                await page.wait_for_timeout(1000)

    # Now merge scraped DOM data with API data
    return self.merge_dom_and_api_data(scraped_data)
```

### Option B: Create New Method (ALTERNATIVE)

Create `async def handle_full_booking_flow(self, page, url)` that:
1. Detects current page type
2. Navigates through ALL steps
3. Scrapes DOM at EACH step
4. Stores scraped data
5. Merges with API data at end

---

## 📊 Data Correlation Strategy

**What we have**:
1. **API data** (already captured): dates, times, some IDs
2. **DOM data** (need to scrape): court names, prices, service names

**How to correlate**:
```python
# From APIs (already captured):
search-timeslots → {datetime: "2025-11-26T22:00", is_bookable: true}
search-staff → {id: 3545010, ...}  # But no name!
search-services → {id: 12345, ...}  # But no price!

# From DOM (need to scrape):
Court page → "Корт №1" (visible text)
Service page → "6,500 ₽" (visible text)

# Final merged record:
{
    'date': '2025-11-26',  # From API datetime
    'time': '22:00',       # From API datetime
    'provider': 'Корт №1', # From DOM scrape!
    'price': '6500 ₽',     # From DOM scrape!
    'service_name': 'Падел-корт, 1 час',  # From DOM scrape!
    'duration': 3600,      # From API or DOM
    'url': original_url
}
```

---

## 🚀 Implementation Steps

1. **IMMEDIATE FIX** (lines 370-472):
   - Modify `handle_time_selection_page` to continue navigation
   - Add DOM scraping at each step
   - Store scraped data in instance variable
   - Merge with API data before returning

2. **TEST**:
   ```bash
   cd /Users/m/git/clients/yclents/yclients-local-fix
   export SUPABASE_URL="https://zojouvfuvdgniqbmbegs.supabase.co"
   export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   python3 test_production_code.py
   ```

3. **VERIFY OUTPUT**:
   - Should have date: "2025-11-26"
   - Should have time: "22:00"
   - Should have provider: "Корт №1"
   - Should have price: "6500 ₽"

---

## 📝 URL Pattern Analysis

```
Multi-location flow:
/select-city/2/select-branch?o=
  ↓ (click branch)
/company/1168982/personal/select-time?o=
  ↓ (select date Nov 26, time 22:00)
/company/1168982/personal/select-time?o=d2526112200
  ↓ (click Продолжить)
/company/1168982/personal/select-master?o=d2526112200
  ↓ (select Корт №1, id 3545010)
/company/1168982/personal/select-master?o=m3545010d2526112200
  ↓ (click Продолжить)
/company/1168982/personal/select-services?o=m3545010d2526112200

Query param format:
- d2526112200 = date (26) + time (2200 = 22:00)
- m3545010 = master/court ID
```

---

## ✅ Success Criteria

After fix, CSV output should contain:
```csv
date,time,price,provider,seat_number,duration,url,service_name,available,extracted_at
2025-11-26,22:00,6500 ₽,Корт №1,,3600,https://b911781.yclients.com/...,Падел-корт 1 час,True,2025-11-02T...
```

**NOT**:
```csv
date,time,price,provider
2025-11-26,22:00,,  ← MISSING DATA!
```

---

## 🔥 Key Insight

**The user's screenshots in the handoff were taken AFTER manually clicking through the flow in reverse order!**

When starting from scratch at `/select-city/2/select-branch`, the flow is:
**TIME → COURT → SERVICE**

Not:
**SERVICE → COURT → TIME**

This explains why the current code doesn't work - it expects the wrong flow order!

---

**Exploration Complete**: 2025-11-02 22:23 UTC
**Next Action**: Modify `handle_time_selection_page` to continue flow and scrape DOM data
