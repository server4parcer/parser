# TDD Test Specifications for YClients Parser

**Comprehensive Test-Driven Development Plan**  
*All tests that must pass before deployment*

---

## 🎯 **Test Categories**

### **1. Unit Tests** - Individual component testing
### **2. Integration Tests** - Component interaction testing  
### **3. E2E Tests** - Full flow validation
### **4. Regression Tests** - Ensure no demo data returns

---

## 📋 **1. Unit Tests**

### **Test Suite: Parser Components**
**File**: `/Users/m/git/clients/yclents/pavel-repo/tests/test_parser_units.py`

```python
import pytest
from datetime import datetime

class TestPriceExtraction:
    """Test price extraction and cleaning."""
    
    def test_clean_price_removes_commas(self):
        """GIVEN: Price with commas '6,000 ₽'
           WHEN: clean_price() is called
           THEN: Returns '6000 ₽' without commas"""
        assert clean_price("6,000 ₽") == "6000 ₽"
    
    def test_clean_price_handles_spaces(self):
        """GIVEN: Price with spaces '12 500 руб'
           WHEN: clean_price() is called  
           THEN: Returns '12500 руб' without spaces"""
        assert clean_price("12 500 руб") == "12500 руб"
    
    def test_clean_price_handles_empty(self):
        """GIVEN: Empty price string
           WHEN: clean_price() is called
           THEN: Returns 'Цена не указана'"""
        assert clean_price("") == "Цена не указана"
    
    def test_price_not_confused_with_time(self):
        """GIVEN: Time value '15:00'
           WHEN: is_price() is called
           THEN: Returns False"""
        assert is_price("15:00") == False
        assert is_price("6000 ₽") == True


class TestDurationParsing:
    """Test duration extraction and conversion."""
    
    def test_parse_hours_to_minutes(self):
        """GIVEN: Duration '1 ч'
           WHEN: parse_duration() is called
           THEN: Returns 60 minutes"""
        assert parse_duration("1 ч") == 60
        assert parse_duration("2 ч") == 120
    
    def test_parse_hours_and_minutes(self):
        """GIVEN: Duration '1 ч 30 мин'
           WHEN: parse_duration() is called
           THEN: Returns 90 minutes"""
        assert parse_duration("1 ч 30 мин") == 90
    
    def test_parse_minutes_only(self):
        """GIVEN: Duration '45 мин'
           WHEN: parse_duration() is called
           THEN: Returns 45 minutes"""
        assert parse_duration("45 мин") == 45
    
    def test_parse_default_duration(self):
        """GIVEN: Empty or invalid duration
           WHEN: parse_duration() is called
           THEN: Returns default 60 minutes"""
        assert parse_duration("") == 60
        assert parse_duration("invalid") == 60


class TestDateParsing:
    """Test date extraction and formatting."""
    
    def test_parse_russian_month(self):
        """GIVEN: Russian date 'август 5'
           WHEN: parse_date() is called
           THEN: Returns '2025-08-05' ISO format"""
        assert parse_date("август", 5, 2025) == "2025-08-05"
    
    def test_parse_numeric_date(self):
        """GIVEN: Numeric date '05.08.2025'
           WHEN: parse_date() is called
           THEN: Returns '2025-08-05' ISO format"""
        assert parse_date("05.08.2025") == "2025-08-05"


class TestSelectorValidation:
    """Test YClients selector detection."""
    
    def test_detect_custom_ui_elements(self):
        """GIVEN: YClients custom element 'ui-kit-simple-cell'
           WHEN: is_valid_selector() is called
           THEN: Returns True"""
        valid_selectors = [
            'ui-kit-simple-cell',
            'ui-kit-headline',
            'ui-kit-title',
            'ui-kit-body'
        ]
        for selector in valid_selectors:
            assert is_valid_yclients_selector(selector) == True
    
    def test_reject_standard_html(self):
        """GIVEN: Standard HTML element 'div'
           WHEN: is_yclients_selector() is called
           THEN: Returns False"""
        assert is_yclients_selector('div') == False
        assert is_yclients_selector('span') == False
```

---

## 📋 **2. Integration Tests**

### **Test Suite: Navigation Flow**
**File**: `/Users/m/git/clients/yclents/pavel-repo/tests/test_navigation_integration.py`

```python
import pytest
from playwright.async_api import async_playwright

class TestYClientsNavigation:
    """Test complete 4-step navigation flow."""
    
    @pytest.mark.asyncio
    async def test_navigate_to_service_selection(self):
        """GIVEN: YClients URL with record-type
           WHEN: Page loads
           THEN: Service selection options are visible"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Navigate to Pavel's working URL
            await page.goto("https://n1165596.yclients.com/company/1109937/record-type?o=")
            
            # Assert service options present
            services = await page.locator('ui-kit-simple-cell').count()
            assert services > 0
            
            # Assert specific service visible
            individual = await page.get_by_text('Индивидуальные услуги').is_visible()
            assert individual == True
            
            await browser.close()
    
    @pytest.mark.asyncio
    async def test_navigate_to_court_selection(self):
        """GIVEN: Service selected
           WHEN: Navigate to court selection
           THEN: Court options are visible"""
        # Test court selection after service click
        # Should see "Корт №1", "Корт №2", etc.
    
    @pytest.mark.asyncio
    async def test_navigate_to_time_selection(self):
        """GIVEN: Court selected
           WHEN: Navigate to time selection
           THEN: Calendar and time slots visible"""
        # Test calendar appears
        # Test time slots like "15:00", "15:30" visible
    
    @pytest.mark.asyncio
    async def test_navigate_to_price_display(self):
        """GIVEN: Time slot selected
           WHEN: Navigate to service packages
           THEN: Prices are visible and extractable"""
        # Test prices appear in format "6,000 ₽"
        # Test duration shown as "1 ч", "1 ч 30 мин"


class TestParserRouter:
    """Test URL routing logic."""
    
    def test_route_yclients_to_playwright(self):
        """GIVEN: YClients URL
           WHEN: Router processes URL
           THEN: Routes to Playwright parser"""
        router = ParserRouter(mock_db)
        
        yclients_urls = [
            "https://n1165596.yclients.com/company/1109937/record-type?o=",
            "https://b861100.yclients.com/company/804153/personal/select-time?o=m-1"
        ]
        
        for url in yclients_urls:
            assert router.is_yclients_url(url) == True
            parser = router.get_parser_for_url(url)
            assert isinstance(parser, YClientsParser)
    
    def test_route_other_to_lightweight(self):
        """GIVEN: Non-YClients URL
           WHEN: Router processes URL
           THEN: Routes to lightweight parser"""
        router = ParserRouter(mock_db)
        
        other_urls = [
            "https://example.com/booking",
            "https://somesite.ru/schedule"
        ]
        
        for url in other_urls:
            assert router.is_yclients_url(url) == False
            parser = router.get_parser_for_url(url)
            assert isinstance(parser, LightweightParser)


class TestDatabaseIntegration:
    """Test database save operations."""
    
    @pytest.mark.asyncio
    async def test_save_real_booking_data(self):
        """GIVEN: Extracted booking data
           WHEN: save_to_database() called
           THEN: Data saved with correct structure"""
        db = DatabaseManager()
        await db.initialize()
        
        test_data = {
            'court_name': 'Корт №1 Ультрапанорамик',
            'date': '2025-08-12',
            'time': '15:00',
            'price': '6000 ₽',
            'duration': 60,
            'venue_name': 'Нагатинская'
        }
        
        success = await db.save_booking_data('test_url', [test_data])
        assert success == True
        
        # Verify saved data
        saved = await db.get_booking_data(limit=1)
        assert len(saved) > 0
        assert saved[0]['court_name'] == test_data['court_name']
```

---

## 📋 **3. End-to-End Tests**

### **Test Suite: Complete Flow**
**File**: `/Users/m/git/clients/yclents/pavel-repo/tests/test_e2e_complete.py`

```python
import pytest
import asyncio

class TestCompleteParsingFlow:
    """Test complete parsing flow from URL to database."""
    
    @pytest.mark.asyncio
    async def test_parse_pavel_venue_e2e(self):
        """GIVEN: Pavel's venue URL
           WHEN: Complete parsing flow runs
           THEN: Real data extracted and saved"""
        
        # Setup
        url = "https://n1165596.yclients.com/company/1109937/record-type?o="
        db = DatabaseManager()
        await db.initialize()
        
        parser = YClientsParser([url], db)
        await parser.initialize()
        
        # Execute
        success, data = await parser.parse_url(url)
        
        # Assert
        assert success == True
        assert len(data) > 0
        
        # Verify data structure
        first_item = data[0]
        assert 'court_name' in first_item
        assert 'price' in first_item
        assert 'time' in first_item
        assert '₽' in first_item['price']
        
        # Verify NO demo data
        assert 'Корт №1 Ультрапанорамик' not in str(data) or first_item['venue_name'] == 'Нагатинская'
        
        await parser.close()
    
    @pytest.mark.asyncio
    async def test_background_scheduling_works(self):
        """GIVEN: Background scheduler configured
           WHEN: 10 minutes pass
           THEN: Parsing runs automatically"""
        
        # Mock time passage
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = None
            
            # Start background task
            task = asyncio.create_task(background_parser_task())
            
            # Verify it runs
            await asyncio.sleep(0.1)  # Let task start
            assert parsing_active == True
            
            task.cancel()
    
    @pytest.mark.asyncio
    async def test_all_pavel_urls_work(self):
        """GIVEN: All Pavel's venue URLs
           WHEN: Each URL is parsed
           THEN: All return data without errors"""
        
        pavel_urls = [
            "https://n1165596.yclients.com/company/1109937/record-type?o=",
            "https://n1308467.yclients.com/company/1192304/record-type?o=",
            "https://b861100.yclients.com/company/804153/personal/select-time?o=m-1",
            "https://b1009933.yclients.com/company/936902/personal/select-time?o=",
            "https://b918666.yclients.com/company/855029/personal/menu?o=m-1"
        ]
        
        results = {}
        for url in pavel_urls:
            router = ParserRouter(Mock())
            data = await router.parse_url(url)
            results[url] = len(data)
        
        # All URLs should return some data or empty list (not crash)
        for url, count in results.items():
            assert isinstance(count, int)
            print(f"✅ {url}: {count} records")
```

---

## 📋 **4. Regression Tests**

### **Test Suite: No Demo Data**
**File**: `/Users/m/git/clients/yclents/pavel-repo/tests/test_no_demo_data.py`

```python
class TestNoDemoDataRegression:
    """Ensure demo data NEVER returns."""
    
    def test_no_generate_demo_method(self):
        """GIVEN: Lightweight parser
           WHEN: Check for generate_demo_data method
           THEN: Method does not exist"""
        from lightweight_parser import YClientsParser
        parser = YClientsParser()
        
        assert not hasattr(parser, 'generate_demo_data')
    
    def test_empty_list_on_failure(self):
        """GIVEN: Invalid URL
           WHEN: Parse fails
           THEN: Returns empty list, not demo data"""
        parser = YClientsParser()
        result = parser.parse_url("https://invalid.url")
        
        assert result == []
        assert len(result) == 0
    
    def test_no_hardcoded_venue_names(self):
        """GIVEN: Any parsing result
           WHEN: Check for demo venue names
           THEN: No hardcoded 'Нагатинская' unless real"""
        
        # These should ONLY appear if from real venue
        demo_indicators = [
            "Корт №1 Ультрапанорамик",
            "Корт №2 Панорамик",
            "Корт №3 Панорамик"
        ]
        
        # Parse a different venue
        other_venue = "https://b861100.yclients.com/company/804153/personal/select-time?o=m-1"
        router = ParserRouter(Mock())
        data = await router.parse_url(other_venue)
        
        # Should NOT contain demo venue courts
        for item in data:
            if 'Нагатинская' not in other_venue:
                assert 'Нагатинская' not in str(item)
    
    @pytest.mark.asyncio
    async def test_database_has_no_fake_data(self):
        """GIVEN: Database after parsing
           WHEN: Query all records
           THEN: No records with impossible combinations"""
        
        db = DatabaseManager()
        await db.initialize()
        
        # Query all data
        all_data = await db.get_booking_data(limit=1000)
        
        for record in all_data:
            # Check for impossible combinations
            if record.get('venue_name') == 'Нагатинская':
                # This is OK if from real venue
                assert 'n1165596.yclients.com' in record.get('url', '')
            
            # Price should not be time
            price = record.get('price', '')
            assert ':' not in price  # No time format in price
            
            # Duration should be realistic
            duration = record.get('duration', 0)
            assert 0 < duration <= 480  # Between 0 and 8 hours
```

---

## 🎯 **Test Execution Plan**

### **Phase 1: Unit Tests** (Run First)
```bash
pytest tests/test_parser_units.py -v
# Expected: 100% pass
```

### **Phase 2: Integration Tests** (After Units Pass)
```bash
pytest tests/test_navigation_integration.py -v
# Expected: 100% pass with real browser
```

### **Phase 3: E2E Tests** (After Integration)
```bash
pytest tests/test_e2e_complete.py -v --timeout=60
# Expected: All Pavel URLs work
```

### **Phase 4: Regression Tests** (Final Check)
```bash
pytest tests/test_no_demo_data.py -v
# Expected: No demo data found
```

### **Full Test Suite**
```bash
pytest tests/ -v --cov=src --cov-report=html
# Expected: >80% coverage, all tests pass
```

---

## ✅ **Test Success Criteria**

### **Must Pass Before Deployment**

| Test Category | Required Coverage | Critical Tests |
|--------------|------------------|----------------|
| Unit Tests | 100% | Price/Duration parsing |
| Integration | 90% | 4-step navigation |
| E2E | 100% | All Pavel URLs |
| Regression | 100% | No demo data |

### **Performance Benchmarks**

- Unit tests: < 5 seconds total
- Integration tests: < 30 seconds per URL
- E2E tests: < 60 seconds per venue
- Full suite: < 5 minutes

### **Quality Gates**

✅ No test failures  
✅ No demo data in any test output  
✅ All Pavel URLs return data  
✅ Database saves real venue information  
✅ Background scheduler activates  
✅ Router correctly identifies URLs  

---

**Next Steps for Implementation**:
1. Create test files in exact paths specified
2. Run tests incrementally (units → integration → E2E)
3. Fix any failures before proceeding
4. Document test results in `/tests/TEST_RESULTS.md`
5. Only deploy after 100% test success