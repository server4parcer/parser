# YClients Parser - Project Completion Guide

**Complete Roadmap for Next Agent**  
*Everything needed to finish and deliver the YClients parser project*

---

## 📂 **Essential Files Created (Read These First!)**

### **1. Discovery Documentation**
- `/ai-docs/YCLIENTS_MCP_DISCOVERIES.md` - Critical findings about YClients structure
- `/ai-docs/PAVEL_VENUES_REFERENCE.md` - All Pavel's real venue URLs and types
- `/ai-docs/CONTEXT_PRIMING.md` - Project context and current state

### **2. Implementation Specifications**
- `/specs/COMPLETE_IMPLEMENTATION_SPEC.md` - Step-by-step implementation guide
- `/specs/TDD_TEST_SPECIFICATIONS.md` - All tests that must pass
- `/specs/REAL_YCLIENTS_INVESTIGATION_SPEC.md` - Investigation methodology

### **3. Modified Files**
- `/lightweight_parser.py` - Demo data removed, JS detection added, background scheduling implemented

---

## 🎯 **Current Project Status**

### **✅ COMPLETED**
1. **Demo data completely removed** - No more fake tennis courts
2. **JavaScript detection implemented** - Identifies SPA pages
3. **Background scheduling added** - Runs every 10 minutes
4. **YClients structure discovered** - 4-step navigation flow documented
5. **Real selectors identified** - Custom UI kit elements found

### **❌ REMAINING WORK**
1. **Implement Playwright parser** with 4-step navigation
2. **Create parser router** to handle URL routing
3. **Write comprehensive tests** for validation
4. **Test with all Pavel's URLs** for verification
5. **Deploy to production** with monitoring

---

## 🚀 **Implementation Checklist**

### **Step 1: Read Documentation** (30 min)
- [ ] Read `/ai-docs/YCLIENTS_MCP_DISCOVERIES.md` - Understand 4-step flow
- [ ] Read `/specs/COMPLETE_IMPLEMENTATION_SPEC.md` - See exact code needed
- [ ] Review Pavel's URLs in `/ai-docs/PAVEL_VENUES_REFERENCE.md`

### **Step 2: Implement Playwright Parser** (2 hours)
- [ ] Open `/src/parser/yclients_parser.py`
- [ ] Add `navigate_yclients_flow()` method from spec
- [ ] Add `extract_time_slots_with_prices()` method
- [ ] Add helper methods: `clean_price()`, `parse_duration()`, `parse_date()`
- [ ] Test with single URL first

### **Step 3: Create Parser Router** (1 hour)
- [ ] Create `/src/parser/parser_router.py`
- [ ] Copy code from `/specs/COMPLETE_IMPLEMENTATION_SPEC.md`
- [ ] Integrate into `/lightweight_parser.py` `run_parser()` function
- [ ] Test routing logic

### **Step 4: Write Tests** (2 hours)
- [ ] Create test files from `/specs/TDD_TEST_SPECIFICATIONS.md`
- [ ] Run unit tests first: `pytest tests/test_parser_units.py -v`
- [ ] Run integration tests: `pytest tests/test_navigation_integration.py -v`
- [ ] Run E2E tests: `pytest tests/test_e2e_complete.py -v`
- [ ] Run regression tests: `pytest tests/test_no_demo_data.py -v`

### **Step 5: Validate with Real URLs** (1 hour)
- [ ] Test each Pavel URL individually:
  ```python
  urls = [
      "https://n1165596.yclients.com/company/1109937/record-type?o=",  # Working venue
      "https://n1308467.yclients.com/company/1192304/record-type?o=",  # Корты-Сетки
      "https://b861100.yclients.com/company/804153/personal/select-time?o=m-1",  # Padel Friends
      "https://b1009933.yclients.com/company/936902/personal/select-time?o=",  # ТК Ракетлон
      "https://b918666.yclients.com/company/855029/personal/menu?o=m-1"  # Padel A33
  ]
  ```
- [ ] Verify real data extracted (courts, prices, times)
- [ ] Confirm NO demo data in results

### **Step 6: Database Verification** (30 min)
- [ ] Check Supabase for saved records
- [ ] Query: `SELECT * FROM booking_data ORDER BY created_at DESC LIMIT 10`
- [ ] Verify real venue names, real prices, real courts
- [ ] Ensure no "Корт №X Ультрапанорамик" unless from actual Нагатинская venue

### **Step 7: Deploy** (30 min)
- [ ] Ensure Playwright installed: `pip install playwright && playwright install chromium`
- [ ] Set environment variables with Pavel's URLs
- [ ] Start system: `python lightweight_parser.py`
- [ ] Monitor logs for successful parsing
- [ ] Check API endpoints work

---

## 🔍 **Critical Discoveries Summary**

### **Why Previous Parser Failed**
1. **YClients is full JavaScript SPA** - No static HTML content
2. **Prices only appear after 4 navigation steps** - Not in initial page
3. **Custom web components** - Uses `ui-kit-*` elements, not standard HTML
4. **Demo data was actually REAL** - "Нагатинская" is Pavel's actual venue!

### **The 4-Step Navigation Flow**
```
1. Service Selection → 2. Court Selection → 3. Date/Time → 4. Service Packages (PRICES HERE!)
```

### **Real Selectors to Use**
```javascript
'ui-kit-simple-cell'  // Service/court containers
'ui-kit-headline'     // Names
'ui-kit-title'        // Prices
'ui-kit-body'         // Duration/details
```

---

## ✅ **Definition of Done**

### **Functional Requirements**
- [ ] Parser navigates all 4 YClients steps
- [ ] Extracts real prices (6000 ₽, not 15:00)
- [ ] Gets actual court names from venues
- [ ] Captures duration in minutes
- [ ] Works with all 5+ Pavel URLs
- [ ] Saves to Supabase successfully

### **Quality Requirements**
- [ ] Zero demo data returned ever
- [ ] All tests pass (unit, integration, E2E, regression)
- [ ] Background scheduling runs automatically
- [ ] Comprehensive logging at each step
- [ ] No crashes on any URL

### **Verification Commands**
```bash
# Test parsing works
curl -X POST http://localhost:8000/parser/run

# Check for real data
curl http://localhost:8000/api/booking-data | jq '.data[0]'

# Verify no demo data
curl http://localhost:8000/api/booking-data | grep -c "Ультрапанорамик"
# Should be 0 unless parsing real Нагатинская venue

# Check background scheduler
tail -f logs/parser.log | grep "автоматического парсинга"
```

---

## 🚨 **Common Pitfalls to Avoid**

1. **Don't skip navigation steps** - Direct URLs won't work
2. **Don't use BeautifulSoup for YClients** - It can't execute JavaScript
3. **Don't hardcode selectors** - Use the discovered `ui-kit-*` elements
4. **Don't ignore wait conditions** - Content loads dynamically
5. **Don't return demo data on failure** - Return empty list

---

## 📞 **Success Indicators**

When complete, you should see:

1. **Logs showing 4-step navigation**:
   ```
   INFO: Step 1: Service selection
   INFO: Step 2: Court selection - Found Корт №1
   INFO: Step 3: Date/time selection - Found 15:00
   INFO: Step 4: Price extraction - Found 6000 ₽
   ```

2. **Database with real venue data**:
   ```
   Корты-Сетки, Padel Friends, ТК Ракетлон, Padel A33
   ```

3. **API returning actual bookings**:
   ```json
   {
     "court_name": "Корт №2",
     "price": "6000 ₽",
     "duration": 60,
     "venue_name": "Корты-Сетки"
   }
   ```

---

## 📋 **Final TODO Summary**

1. ✅ Document discoveries (DONE)
2. ✅ Create specifications (DONE)
3. ✅ Remove demo data (DONE)
4. ⏳ **Implement Playwright parser** ← START HERE
5. ⏳ Create router
6. ⏳ Write tests
7. ⏳ Test all URLs
8. ⏳ Verify database
9. ⏳ Deploy
10. ⏳ Final validation

---

**🎯 Next Action**: Open `/specs/COMPLETE_IMPLEMENTATION_SPEC.md` and start implementing the Playwright parser with 4-step navigation. All code is provided there - just copy and adapt to existing structure.

**Time Estimate**: 6-8 hours to complete all remaining work

**Success Metric**: All Pavel's venues return real booking data with zero demo fallbacks