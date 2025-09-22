# Real YClients Investigation & Fix Specification

**Human Behavior MCP Investigation Plan**  
*Comprehensive specification for investigating Pavel's real YClients URLs and implementing fixes*

---

## 🎯 **Project Overview**

### **Objective**
Investigate Pavel's real YClients URLs using human behavior MCP to understand actual page structure, then fix parsing to extract real data instead of demo fallback.

### **Pavel's Real URLs & Venues**
```
1. Корты-Сетки (Tennis Courts):
   https://n1308467.yclients.com/company/1192304/record-type?o=

2. Multi-location Club (3 branches):
   https://b911781.yclients.com/select-city/2/select-branch?o=

3. Working Venue:
   https://n1165596.yclients.com/company/1109937/record-type?o=

4. Padel Friends:
   https://b861100.yclients.com/company/804153/personal/select-time?o=m-1

5. ТК "Ракетлон" (Tennis Club):
   https://b1009933.yclients.com/company/936902/personal/select-time?o=

6. Padel A33:
   https://b918666.yclients.com/company/855029/personal/menu?o=m-1
```

---

## 📋 **Phase 1: Human Behavior MCP Investigation**
*Priority: CRITICAL | Timeline: Immediate*

### **1.1 URL Pattern Analysis**
**Observation Goals**:
- **Service Selection Pages**: URLs ending with `record-type?o=`
- **Direct Booking Pages**: URLs with `personal/select-time?o=`
- **Menu Pages**: URLs with `personal/menu?o=`
- **Multi-location**: URLs with `select-city/select-branch`

### **1.2 Navigation Flow Investigation**
**For Each URL Type**:

#### **Service Selection (`record-type?o=`)**
1. **Load page** with human behavior MCP
2. **Screenshot** initial state
3. **Inspect DOM** for service options
4. **Click service** → Navigate to booking page
5. **Document** navigation path and final URL structure

#### **Direct Booking (`personal/select-time`)**
1. **Load page** with human delay simulation
2. **Check calendar** availability
3. **Click date** → Check time slots load
4. **Inspect time slot elements** for actual selectors
5. **Document** price, time, provider extraction patterns

#### **Menu Pages (`personal/menu`)**
1. **Load page** and wait for full render
2. **Screenshot** menu structure
3. **Navigate** through booking flow
4. **Document** complete user journey

### **1.3 Real Selector Discovery**
**For Each Page Type, Document**:
```javascript
// Time slot selectors
.actual-time-class
[data-time-attribute]
// Price selectors  
.actual-price-class
[data-price-attribute]
// Provider/staff selectors
.actual-staff-class
// Service selectors
.actual-service-class
```

### **1.4 Dynamic Content Analysis**
**Check For**:
- **AJAX loading** after user interactions
- **Required waits** for content to appear
- **Anti-bot protections** (CAPTCHAs, blocks)
- **JavaScript requirements** for full functionality

---

## 📋 **Phase 2: Parsing Logic Analysis**
*Priority: HIGH | Timeline: After Phase 1*

### **2.1 Current Parser Audit**
**File**: `lightweight_parser.py`

**Current Issues Found**:
```python
# Line 91: Demo fallback on ANY exception
except Exception as e:
    return self.generate_demo_data(url)  # ❌ WRONG

# Line 162: Demo fallback if no data found
if not booking_data:
    booking_data = self.generate_demo_data(url)  # ❌ WRONG

# Lines 99-105: Generic selectors that may not match real YClients
time_elements = soup.find_all(text=re.compile(r'\d{1,2}:\d{2}'))
price_elements = soup.find_all(text=re.compile(r'\d+\s*₽|\d+\s*руб'))
```

### **2.2 Selector Validation**
**Test Current Patterns Against Real Pages**:
- Do time patterns actually exist in HTML?
- Are prices in expected format?
- Do service patterns match real venue names?

---

## 📋 **Phase 3: Implementation Plan**
*Priority: HIGH | Timeline: After Phase 2*

### **3.1 Demo Data Elimination**
**Files to Modify**:
- `lightweight_parser.py:91` → `return []`
- `lightweight_parser.py:162` → `booking_data = []`
- `lightweight_parser.py:166` → `booking_data = []`
- Delete `generate_demo_data()` method entirely

### **3.2 Real Selector Implementation**
**Based on MCP Findings**:
```python
# Replace with real selectors found during investigation
def extract_real_yclients_data(self, soup: BeautifulSoup, url: str):
    # Use actual selectors discovered via MCP
    time_slots = soup.select('[actual-time-selector]')
    prices = soup.select('[actual-price-selector]')
    providers = soup.select('[actual-provider-selector]')
    
    # Real extraction logic based on findings
```

### **3.3 Navigation Flow Handling**
**For Different URL Types**:
```python
def handle_yclients_url(self, url: str):
    if 'record-type' in url:
        return self.handle_service_selection(url)
    elif 'personal/select-time' in url:
        return self.handle_direct_booking(url)
    elif 'personal/menu' in url:
        return self.handle_menu_page(url)
    elif 'select-city' in url:
        return self.handle_multi_location(url)
```

### **3.4 Background Scheduling**
**Add to `lightweight_parser.py`**:
```python
async def background_parser_task():
    """Background parsing every 10 minutes"""
    while True:
        try:
            await run_parser()
            await asyncio.sleep(PARSE_INTERVAL)
        except Exception as e:
            logger.error(f"Background parser error: {e}")
            await asyncio.sleep(60)

# Startup modification
if __name__ == "__main__":
    # Start background task + API server concurrently
    asyncio.run(asyncio.gather(
        background_parser_task(),
        run_api_server()
    ))
```

---

## 📋 **Phase 4: Testing & Validation**
*Priority: MEDIUM | Timeline: After Phase 3*

### **4.1 Real URL Testing**
**Test Suite**:
```python
def test_real_urls():
    """Test all Pavel's URLs with real parser"""
    pavel_urls = [
        "https://n1308467.yclients.com/company/1192304/record-type?o=",
        "https://n1165596.yclients.com/company/1109937/record-type?o=",
        "https://b861100.yclients.com/company/804153/personal/select-time?o=m-1",
        # ... rest of Pavel's URLs
    ]
    
    for url in pavel_urls:
        result = parser.parse_url(url)
        # Verify NO demo data
        assert not any("Корт №1 Ультрапанорамик" in str(item) for item in result)
        # Verify real data structure
        if result:  # If data found
            assert all(item.get('venue_name') != 'Нагатинская' for item in result)
```

### **4.2 Database Verification**
```bash
# Check database contains real data
curl http://localhost:8000/api/booking-data | jq '.data[] | select(.provider | contains("Корт №"))'
# Should return empty - no demo data

# Check for real venue names
curl http://localhost:8000/api/booking-data | jq '.data[] | select(.location_name | contains("Корты-Сетки", "Padel", "Ракетлон"))'
# Should return real venues from Pavel's URLs
```

---

## 🎯 **Success Metrics**

### **Investigation Success**
- [ ] All 6 Pavel URLs successfully loaded via MCP
- [ ] Real selectors documented for each URL type
- [ ] Navigation flow mapped for each venue type
- [ ] Dynamic content loading requirements identified

### **Implementation Success**
- [ ] Zero demo data returned from any URL
- [ ] Real data extracted from at least 80% of Pavel's URLs
- [ ] Background scheduling working (10-minute intervals)
- [ ] Database contains real venue data only

### **Quality Metrics**
- [ ] No "Корт №1 Ультрапанорамик" in any response
- [ ] No "Нагатинская" location in database
- [ ] Real venue names: "Корты-Сетки", "Padel Friends", "Ракетлон", "Padel A33"
- [ ] Accurate prices in rubles (not time values)

---

## 🔍 **Investigation Priority Order**

### **Start With**:
1. **Most Reliable**: `https://n1165596.yclients.com/company/1109937/record-type?o=` (Pavel said working)
2. **Tennis Focus**: `https://n1308467.yclients.com/company/1192304/record-type?o=` (Корты-Сетки)
3. **Direct Booking**: `https://b861100.yclients.com/company/804153/personal/select-time?o=m-1` (Padel Friends)

### **Then Expand To**:
4. Multi-location handling
5. Menu-based navigation
6. Different venue types (Tennis vs Padel)

---

**🎯 Next Action**: Start human behavior MCP investigation with the working URL to understand real YClients page structure and navigation flow.