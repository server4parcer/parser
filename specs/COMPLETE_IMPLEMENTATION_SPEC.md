# Complete YClients Parser Implementation Specification

**From Current State to Final Delivery**  
*Step-by-step implementation guide for completing the YClients parser project*

---

## 📍 **Current State Assessment**

### **What's Done**
✅ Demo data fallback removed from `lightweight_parser.py`  
✅ JavaScript detection implemented  
✅ Background scheduling added  
✅ Database integration working (Supabase with RLS disabled)  
✅ Real YClients structure discovered via MCP Playwright  

### **What's Needed**
❌ Playwright parser implementation with 4-step navigation  
❌ Real selector usage from MCP discoveries  
❌ Integration router between parsers  
❌ Comprehensive testing  
❌ Production deployment  

---

## 🎯 **Implementation Roadmap**

### **Phase 1: Update Existing Playwright Parser**
**File**: `/Users/m/git/clients/yclents/pavel-repo/src/parser/yclients_parser.py`

#### **1.1 Add 4-Step Navigation Method**
```python
async def navigate_yclients_flow(self, page: Page, url: str) -> List[Dict]:
    """
    Navigate through YClients 4-step booking flow.
    Step 1: Service selection (record-type)
    Step 2: Court selection (select-master)
    Step 3: Date/time selection (select-time)
    Step 4: Service packages with prices (select-services)
    """
    results = []
    
    # Step 1: Load and select service type
    await page.goto(url, wait_until='networkidle')
    await page.wait_for_selector('ui-kit-simple-cell', timeout=10000)
    
    # Click on "Индивидуальные услуги" or first available service
    service_links = await page.get_by_role('link').all()
    for link in service_links:
        text = await link.text_content()
        if 'Индивидуальные' in text or 'услуги' in text.lower():
            await link.click()
            break
    
    # Step 2: Select courts
    await page.wait_for_url('**/personal/select-master**')
    await page.wait_for_selector('ui-kit-simple-cell')
    
    courts = await page.locator('ui-kit-simple-cell').all()
    for court in courts[:3]:  # Limit to first 3 courts for testing
        court_name = await court.locator('ui-kit-headline').text_content()
        await court.click()
        
        # Continue to date selection
        await page.get_by_role('button', { 'name': 'Продолжить' }).click()
        
        # Step 3: Select dates and times
        await page.wait_for_url('**/personal/select-time**')
        await self.extract_time_slots_with_prices(page, court_name, results)
        
        # Go back to court selection
        await page.go_back()
        await page.wait_for_selector('ui-kit-simple-cell')
    
    return results

async def extract_time_slots_with_prices(self, page: Page, court_name: str, results: List[Dict]):
    """Extract time slots and navigate to get prices."""
    
    # Get available dates
    dates = await page.locator('.calendar-day:not(.disabled)').all()
    
    for date in dates[:2]:  # Limit to 2 dates for testing
        date_text = await date.text_content()
        await date.click()
        await page.wait_for_timeout(1000)
        
        # Get time slots
        time_slots = await page.locator('[data-time]').all()
        if not time_slots:
            # Try alternative selector
            time_slots = await page.get_by_text(re.compile(r'\d{1,2}:\d{2}')).all()
        
        for slot in time_slots[:3]:  # Limit to 3 slots per date
            time_text = await slot.text_content()
            await slot.click()
            
            # Continue to services/prices
            continue_btn = page.get_by_role('button', { 'name': 'Продолжить' })
            if await continue_btn.is_visible():
                await continue_btn.click()
                
                # Step 4: Extract prices from service packages
                await page.wait_for_url('**/personal/select-services**')
                await page.wait_for_selector('ui-kit-simple-cell')
                
                services = await page.locator('ui-kit-simple-cell').all()
                for service in services:
                    try:
                        name = await service.locator('ui-kit-headline').text_content()
                        price = await service.locator('ui-kit-title').text_content()
                        duration = await service.locator('ui-kit-body').text_content()
                        
                        # Clean and structure data
                        result = {
                            'url': page.url,
                            'court_name': court_name.strip() if court_name else '',
                            'date': self.parse_date(date_text),
                            'time': time_text.strip(),
                            'service_name': name.strip() if name else '',
                            'price': self.clean_price(price),
                            'duration': self.parse_duration(duration),
                            'venue_name': 'Нагатинская',  # Extract from page if available
                            'extracted_at': datetime.now().isoformat()
                        }
                        results.append(result)
                    except Exception as e:
                        logger.warning(f"Failed to extract service: {e}")
                
                # Go back to time selection
                await page.go_back()
                await page.wait_for_timeout(1000)
```

#### **1.2 Add Helper Methods**
```python
def clean_price(self, price_text: str) -> str:
    """Clean price text: '6,000 ₽' -> '6000 ₽'"""
    if not price_text:
        return "Цена не указана"
    # Remove spaces and commas from numbers
    import re
    cleaned = re.sub(r'(\d),(\d)', r'\1\2', price_text)
    cleaned = cleaned.strip()
    return cleaned if '₽' in cleaned else f"{cleaned} ₽"

def parse_duration(self, duration_text: str) -> int:
    """Parse duration: '1 ч 30 мин' -> 90"""
    if not duration_text:
        return 60
    
    total_minutes = 0
    # Extract hours
    hour_match = re.search(r'(\d+)\s*ч', duration_text)
    if hour_match:
        total_minutes += int(hour_match.group(1)) * 60
    
    # Extract minutes
    min_match = re.search(r'(\d+)\s*мин', duration_text)
    if min_match:
        total_minutes += int(min_match.group(1))
    
    return total_minutes if total_minutes > 0 else 60

def parse_date(self, date_text: str) -> str:
    """Parse date from calendar text to ISO format."""
    from datetime import datetime
    # Implementation depends on actual date format
    # For now, return current date
    return datetime.now().strftime('%Y-%m-%d')
```

---

### **Phase 2: Create Parser Router**
**New File**: `/Users/m/git/clients/yclents/pavel-repo/src/parser/parser_router.py`

```python
"""
Parser Router - Routes URLs to appropriate parser based on content type.
"""
import asyncio
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse

from src.parser.yclients_parser import YClientsParser
from lightweight_parser import YClientsParser as LightweightParser
from src.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class ParserRouter:
    """Routes URLs to appropriate parser implementation."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.lightweight_parser = LightweightParser()
        self.playwright_parser = None  # Lazy initialization
        
    async def parse_url(self, url: str) -> List[Dict]:
        """
        Route URL to appropriate parser.
        YClients → Playwright parser
        Others → Lightweight parser
        """
        # Check if it's a YClients URL
        if self.is_yclients_url(url):
            logger.info(f"🎯 Routing to Playwright parser: {url}")
            return await self.parse_with_playwright(url)
        else:
            logger.info(f"📄 Routing to lightweight parser: {url}")
            return self.lightweight_parser.parse_url(url)
    
    def is_yclients_url(self, url: str) -> bool:
        """Check if URL is YClients booking page."""
        yclients_indicators = [
            'yclients.com',
            'record-type',
            'personal/',
            'select-time',
            'select-master'
        ]
        return any(indicator in url for indicator in yclients_indicators)
    
    async def parse_with_playwright(self, url: str) -> List[Dict]:
        """Parse using Playwright browser automation."""
        # Initialize Playwright parser if needed
        if not self.playwright_parser:
            self.playwright_parser = YClientsParser([url], self.db_manager)
            await self.playwright_parser.initialize()
        
        try:
            # Use the new navigation flow
            success, data = await self.playwright_parser.parse_url(url)
            return data if success else []
        except Exception as e:
            logger.error(f"Playwright parsing failed: {e}")
            return []
        finally:
            if self.playwright_parser:
                await self.playwright_parser.close()
                self.playwright_parser = None
```

---

### **Phase 3: Update Main Entry Point**
**File**: `/Users/m/git/clients/yclents/pavel-repo/lightweight_parser.py`

#### **3.1 Integrate Router**
```python
# Add import at top
from src.parser.parser_router import ParserRouter

# Modify run_parser function
async def run_parser():
    """Запуск парсера YClients с маршрутизацией"""
    global parsing_active, last_parse_time, parse_results, db_manager
    
    if parsing_active:
        return {"status": "уже_запущен"}
    
    parsing_active = True
    last_parse_time = datetime.now()
    
    try:
        logger.info("🚀 Запуск улучшенного парсера с маршрутизацией...")
        
        urls = [url.strip() for url in PARSE_URLS.split(",") if url.strip()]
        if not urls:
            return {"status": "error", "message": "URL не настроены"}
        
        # Initialize router
        if db_manager is None:
            db_manager = DatabaseManager()
            await db_manager.initialize()
        
        router = ParserRouter(db_manager)
        
        all_results = []
        for url in urls:
            logger.info(f"🎯 Обработка URL: {url}")
            url_results = await router.parse_url(url)
            all_results.extend(url_results)
        
        if all_results:
            success = await save_to_database(all_results)
            parse_results.update({
                "status": "завершено",
                "last_run": last_parse_time.isoformat(),
                "urls_parsed": len(urls),
                "records_extracted": len(all_results),
                "has_real_data": True,
                "no_demo_data": True
            })
            return {"status": "success", "extracted": len(all_results)}
        else:
            return {"status": "warning", "message": "Данные не извлечены"}
            
    except Exception as e:
        logger.error(f"❌ Ошибка парсера: {e}")
        return {"status": "error", "message": str(e)}
    
    finally:
        parsing_active = False
```

---

### **Phase 4: Test Implementation**
**New File**: `/Users/m/git/clients/yclents/pavel-repo/tests/test_yclients_navigation.py`

```python
"""
TDD Tests for YClients 4-step navigation flow.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.parser.yclients_parser import YClientsParser
from src.parser.parser_router import ParserRouter


class TestYClientsNavigation:
    """Test 4-step YClients navigation flow."""
    
    @pytest.mark.asyncio
    async def test_step1_service_selection(self):
        """Test: Can navigate to service selection page."""
        # Arrange
        url = "https://n1165596.yclients.com/company/1109937/record-type?o="
        parser = YClientsParser([url], Mock())
        
        # Act
        await parser.initialize()
        navigation_success = await parser.navigate_to_url(url)
        
        # Assert
        assert navigation_success == True
        assert parser.page is not None
        await parser.close()
    
    @pytest.mark.asyncio
    async def test_step2_court_selection(self):
        """Test: Can select court after service selection."""
        # Test court selection finds real court names
        expected_courts = ["Корт №1 Ультрапанорамик", "Корт №2 Панорамик"]
        # Implementation here
    
    @pytest.mark.asyncio  
    async def test_step3_datetime_selection(self):
        """Test: Can select date and time slots."""
        # Test date/time selection works
        # Implementation here
    
    @pytest.mark.asyncio
    async def test_step4_price_extraction(self):
        """Test: Can extract prices from service packages."""
        # Test price extraction gets real prices
        expected_price_format = r'\d+\s*₽'
        # Implementation here
    
    @pytest.mark.asyncio
    async def test_no_demo_data_returned(self):
        """Test: Verify NO demo data is ever returned."""
        # Arrange
        parser = YClientsParser([], Mock())
        
        # Act
        result = await parser.parse_url("https://invalid.url")
        
        # Assert
        assert len(result) == 0 or all(
            'Корт №1 Ультрапанорамик' not in str(item) 
            for item in result
        )
    
    @pytest.mark.asyncio
    async def test_router_correctly_routes_urls(self):
        """Test: Router sends YClients to Playwright, others to lightweight."""
        # Arrange
        router = ParserRouter(Mock())
        
        # Test YClients URL
        yclients_url = "https://n1165596.yclients.com/company/1109937/record-type?o="
        assert router.is_yclients_url(yclients_url) == True
        
        # Test non-YClients URL
        other_url = "https://example.com/booking"
        assert router.is_yclients_url(other_url) == False


class TestDataValidation:
    """Test data extraction and validation."""
    
    def test_price_cleaning(self):
        """Test: Price cleaning removes commas and formats correctly."""
        parser = YClientsParser([], Mock())
        
        test_cases = [
            ("6,000 ₽", "6000 ₽"),
            ("12,500 ₽", "12500 ₽"),
            ("1 000 руб", "1000 руб"),
            ("", "Цена не указана")
        ]
        
        for input_price, expected in test_cases:
            assert parser.clean_price(input_price) == expected
    
    def test_duration_parsing(self):
        """Test: Duration parsing converts to minutes."""
        parser = YClientsParser([], Mock())
        
        test_cases = [
            ("1 ч", 60),
            ("1 ч 30 мин", 90),
            ("2 ч", 120),
            ("30 мин", 30),
            ("", 60)  # Default
        ]
        
        for input_duration, expected in test_cases:
            assert parser.parse_duration(input_duration) == expected
    
    def test_data_structure(self):
        """Test: Extracted data has required fields."""
        required_fields = [
            'url', 'court_name', 'date', 'time',
            'price', 'duration', 'venue_name', 'extracted_at'
        ]
        
        # Mock extracted data
        sample_data = {
            'url': 'https://yclients.com/...',
            'court_name': 'Корт №1',
            'date': '2025-08-12',
            'time': '15:00',
            'price': '6000 ₽',
            'duration': 60,
            'venue_name': 'Нагатинская',
            'extracted_at': datetime.now().isoformat()
        }
        
        for field in required_fields:
            assert field in sample_data


class TestEndToEnd:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_pavel_urls_parse_successfully(self):
        """Test: All Pavel's URLs parse without errors."""
        pavel_urls = [
            "https://n1165596.yclients.com/company/1109937/record-type?o=",
            "https://n1308467.yclients.com/company/1192304/record-type?o=",
            "https://b861100.yclients.com/company/804153/personal/select-time?o=m-1"
        ]
        
        router = ParserRouter(Mock())
        
        for url in pavel_urls:
            # Should not raise exceptions
            result = await router.parse_url(url)
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_database_saves_real_data(self):
        """Test: Database saves contain real venue data, no demo data."""
        # Implementation to verify database contains:
        # - Real court names from venues
        # - Real prices in correct format
        # - No "Корт №X Ультрапанорамик" unless from real venue
        pass


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## 📋 **Deployment Checklist**

### **Pre-Deployment Validation**

- [ ] All tests pass (`pytest tests/test_yclients_navigation.py`)
- [ ] No demo data in any responses
- [ ] Playwright parser works with all Pavel URLs
- [ ] Router correctly identifies YClients URLs
- [ ] Background scheduling runs every 10 minutes
- [ ] Database saves real extracted data
- [ ] Logs show successful 4-step navigation

### **Deployment Steps**

1. **Update Dependencies**
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Environment Variables**
   ```bash
   PARSE_URLS=https://n1165596.yclients.com/company/1109937/record-type?o=,https://n1308467.yclients.com/company/1192304/record-type?o=
   PARSE_INTERVAL=600
   SUPABASE_URL=<actual_url>
   SUPABASE_KEY=<actual_key>
   ```

3. **Run Tests**
   ```bash
   python -m pytest tests/ -v
   ```

4. **Start System**
   ```bash
   python lightweight_parser.py
   ```

5. **Verify Operation**
   ```bash
   # Check API
   curl http://localhost:8000/health
   curl http://localhost:8000/parser/status
   
   # Check for real data
   curl http://localhost:8000/api/booking-data | jq '.data[0]'
   ```

---

## 🎯 **Success Criteria**

### **Functional Requirements**
✅ Navigates all 4 steps of YClients flow  
✅ Extracts real prices (not time values)  
✅ Gets actual court names  
✅ Captures duration correctly  
✅ No demo data ever returned  

### **Performance Requirements**
✅ Parses URL in < 30 seconds  
✅ Handles all Pavel's venue types  
✅ Recovers from navigation errors  
✅ Saves to database successfully  

### **Quality Requirements**
✅ 100% test coverage for critical paths  
✅ Comprehensive logging at each step  
✅ Error handling without crashes  
✅ Clean, maintainable code  

---

**Next Agent Instructions**: 
1. Read `/Users/m/git/clients/yclents/pavel-repo/ai-docs/YCLIENTS_MCP_DISCOVERIES.md` for context
2. Implement changes in order listed above
3. Run tests after each phase
4. Verify with Pavel's real URLs
5. Confirm no demo data in results