# Real YClients Parsing Implementation Specification

**Comprehensive Project Plan**  
*Detailed specification for fixing demo data fallback and implementing real YClients parsing*

---

## 🎯 **Project Overview**

### **Objective**
Replace demo data fallback system with real YClients parsing to extract genuine booking information from YClients platform pages.

### **Current State Analysis**
- ✅ **Database Fixed**: Supabase RLS disabled, saves working
- ❌ **Demo Data Problem**: `lightweight_parser.py` returns fake tennis data
- ❌ **No Auto Scheduling**: Manual parsing only
- ❌ **Incomplete Duration**: Hardcoded 60 minutes
- ❌ **Poor Navigation**: Limited YClients flow handling

### **Success Criteria**
1. Zero demo data returned - only real YClients data or empty results
2. Automatic parsing every 10 minutes via background scheduler
3. Real duration values extracted from YClients pages
4. Proper YClients booking flow navigation
5. 95%+ data accuracy for valid YClients URLs

---

## 📋 **Phase 1: Remove Demo Data Fallback** 
*Priority: CRITICAL | Timeline: Immediate*

### **Tasks**

#### **1.1 Eliminate Demo Data Generation**
**File**: `lightweight_parser.py`
**Changes**:
```python
# REMOVE (lines 88-91):
except Exception as e:
    logger.error(f"❌ Ошибка парсинга {url}: {e}")
    return self.generate_demo_data(url)  # ❌ DELETE

# REPLACE WITH:
except Exception as e:
    logger.error(f"❌ Ошибка парсинга {url}: {e}")
    return []  # ✅ Return empty list
```

#### **1.2 Delete Demo Data Method**
**Action**: Remove entire `generate_demo_data()` method (lines 170-222)
**Impact**: Eliminates source of fake tennis court data

#### **1.3 Remove Additional Fallbacks**
**Locations**:
- Line 162: `booking_data = self.generate_demo_data(url)`
- Line 166: `booking_data = self.generate_demo_data(url)`
**Change**: Replace with `return []`

#### **1.4 Verification Tests**
```python
# Test that no demo data is returned
def test_no_demo_data():
    parser = YClientsParser()
    result = parser.parse_url("invalid_url")
    assert result == []
    assert "Корт №1 Ультрапанорамик" not in str(result)
```

---

## 📋 **Phase 2: Implement Background Scheduling**
*Priority: HIGH | Timeline: After Phase 1*

### **Tasks**

#### **2.1 Background Parser Task**
**File**: `lightweight_parser.py`
**Add Function**:
```python
async def background_parser_task():
    """Background task for automatic parsing every 10 minutes"""
    global parsing_active, parse_results
    
    while True:
        try:
            if not parsing_active:  # Prevent overlapping runs
                logger.info("🔄 Starting scheduled parse...")
                await run_parser()
                logger.info(f"⏰ Next parse in {PARSE_INTERVAL} seconds")
            else:
                logger.info("⏳ Parse already running, skipping...")
            
            await asyncio.sleep(PARSE_INTERVAL)
            
        except Exception as e:
            logger.error(f"❌ Background parser error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error
```

#### **2.2 Startup Integration**
**File**: `lightweight_parser.py` (main block)
**Modify**:
```python
if __name__ == "__main__":
    # System checks (existing code)...
    
    # Start background parser
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Create background task
    background_task = loop.create_task(background_parser_task())
    
    # Create API server task
    api_task = loop.create_task(run_api_server())
    
    # Run both concurrently
    try:
        loop.run_until_complete(asyncio.gather(
            background_task,
            api_task
        ))
    except KeyboardInterrupt:
        logger.info("👋 Stopping background parser...")
    finally:
        loop.close()
```

#### **2.3 API Server Extraction**
**Add Function**:
```python
async def run_api_server():
    """Run FastAPI server as async task"""
    config = uvicorn.Config(
        app=app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()
```

---

## 📋 **Phase 3: Real Duration Parsing**
*Priority: MEDIUM | Timeline: After Phase 2*

### **Tasks**

#### **3.1 Duration Extractor Method**
**File**: `src/parser/production_data_extractor.py`
**Add Method**:
```python
async def find_duration_in_slot(self, slot_element: ElementHandle) -> int:
    """Extract booking duration from YClients slot element."""
    try:
        # Duration-specific selectors
        duration_selectors = [
            ".duration", ".time-duration", ".service-duration",
            ".booking-duration", ".slot-duration",
            "[data-duration]", "[data-time-duration]"
        ]
        
        for selector in duration_selectors:
            element = await slot_element.query_selector(selector)
            if element:
                duration_text = await self.extract_text_safely(element)
                
                # Parse duration patterns
                patterns = [
                    r'(\d+)\s*мин',         # "60 мин"
                    r'(\d+)\s*min',         # "60 min"
                    r'(\d+)\s*час',         # "1 час"
                    r'(\d+)\s*hour',        # "1 hour"
                    r'(\d+)h',              # "1h"
                    r'(\d+):(\d+)',         # "1:30" (hour:min)
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, duration_text.lower())
                    if match:
                        if ':' in pattern:  # Hour:minute format
                            hours, minutes = int(match.group(1)), int(match.group(2))
                            return hours * 60 + minutes
                        else:
                            value = int(match.group(1))
                            if 'час' in duration_text or 'hour' in duration_text:
                                return value * 60
                            return value  # Already in minutes
        
        # Check data attributes
        duration_attr = await slot_element.get_attribute('data-duration')
        if duration_attr:
            try:
                return int(duration_attr)
            except ValueError:
                pass
        
        logger.debug("❌ No duration found, using default 60 minutes")
        return 60  # Default fallback
        
    except Exception as e:
        logger.error(f"❌ Duration extraction error: {e}")
        return 60
```

#### **3.2 Integration with Data Extraction**
**File**: `src/parser/production_data_extractor.py`
**Modify** `extract_slot_data_production`:
```python
async def extract_slot_data_production(self, slot_element: ElementHandle) -> Dict[str, Any]:
    # Existing extractions...
    
    # Add duration extraction
    duration_value = await self.find_duration_in_slot(slot_element)
    result['duration'] = duration_value
    
    logger.info(f"📊 Extracted: time={result.get('time')}, price={result.get('price')}, duration={duration_value}min")
    
    return result
```

---

## 📋 **Phase 4: Enhanced YClients Navigation**
*Priority: MEDIUM | Timeline: After Phase 3*

### **Tasks**

#### **4.1 Service Selection Handler Enhancement**
**File**: `src/parser/yclients_parser.py`
**Improve** `handle_service_selection_page`:
```python
async def handle_service_selection_page(self, url: str) -> List[str]:
    """Enhanced service selection with better error handling"""
    logger.info(f"🎯 Enhanced service selection: {url}")
    direct_urls = []
    
    try:
        if not await self.navigate_to_url(url):
            logger.error(f"Failed to load service selection page: {url}")
            return []
        
        # Wait for services to load with multiple selectors
        service_loaded = False
        selectors_to_try = [
            '.service-item', '.service-option', '.record__service',
            '.ycwidget-service', '.booking-service-item',
            '[data-service-id]', '.service-list .service'
        ]
        
        for selector in selectors_to_try:
            try:
                await self.page.wait_for_selector(selector, timeout=5000)
                service_loaded = True
                break
            except:
                continue
        
        if not service_loaded:
            logger.warning("No service elements found, trying to parse page anyway")
            return await self.extract_booking_urls_from_page()
        
        # Enhanced service extraction logic
        # ... (detailed implementation)
        
    except Exception as e:
        logger.error(f"Service selection error: {e}")
        return []
```

#### **4.2 Booking URL Extraction**
**Add Method**:
```python
async def extract_booking_urls_from_page(self) -> List[str]:
    """Extract booking URLs from any YClients page"""
    urls = []
    
    try:
        # Look for booking-related links
        link_selectors = [
            'a[href*="booking"]',
            'a[href*="record"]', 
            'a[href*="book"]',
            '[data-booking-url]'
        ]
        
        for selector in link_selectors:
            elements = await self.page.query_selector_all(selector)
            for element in elements:
                href = await element.get_attribute('href')
                if href and self.is_valid_booking_url(href):
                    if href.startswith('/'):
                        base = '/'.join(self.page.url.split('/')[:3])
                        href = base + href
                    urls.append(href)
        
        return list(set(urls))  # Remove duplicates
        
    except Exception as e:
        logger.error(f"URL extraction error: {e}")
        return []

def is_valid_booking_url(self, url: str) -> bool:
    """Validate if URL is a booking-related URL"""
    booking_indicators = ['booking', 'record', 'book', 'reserve']
    return any(indicator in url.lower() for indicator in booking_indicators)
```

---

## 📋 **Phase 5: Data Validation & Quality**
*Priority: MEDIUM | Timeline: Concurrent with other phases*

### **Tasks**

#### **5.1 Enhanced Price Validation**
**File**: `src/database/db_manager.py`
**Improve** `is_time_format`:
```python
def is_time_format(self, value: str) -> bool:
    """Enhanced time format detection"""
    if not value:
        return False
        
    value = value.strip()
    
    # Time patterns
    time_patterns = [
        r'^\d{1,2}:\d{2}$',           # 10:00
        r'^\d{1,2}:\d{2}:\d{2}$',     # 10:00:00
        r'^\d{1,2}\.\d{2}$',          # 10.00
    ]
    
    for pattern in time_patterns:
        if re.match(pattern, value):
            return True
    
    # Suspicious currency patterns (hour with currency)
    suspicious_patterns = [
        r'^([0-2]?\d)\s*[₽Рруб$€]',   # 0-23 with currency
        r'^([0-2]?\d)\s*руб',         # 0-23 with "руб"
    ]
    
    for pattern in suspicious_patterns:
        match = re.match(pattern, value, re.IGNORECASE)
        if match:
            hour = int(match.group(1))
            if 0 <= hour <= 23:
                return True  # Likely hour disguised as price
    
    return False
```

#### **5.2 Data Completeness Validation**
**Add Method**:
```python
def validate_booking_record(self, record: Dict) -> Tuple[bool, List[str]]:
    """Validate booking record completeness and quality"""
    issues = []
    
    # Required fields
    required = ['date', 'time', 'price']
    for field in required:
        if not record.get(field):
            issues.append(f"Missing {field}")
    
    # Data quality checks
    if self.is_time_format(record.get('price', '')):
        issues.append("Price appears to be time format")
    
    if record.get('provider') == record.get('price'):
        issues.append("Provider and price are identical")
    
    if len(record.get('price', '')) < 2:
        issues.append("Price too short")
    
    return len(issues) == 0, issues
```

---

## 🧪 **Testing Strategy**

### **Unit Tests**
```python
# tests/test_real_parsing.py
class TestRealParsing:
    def test_no_demo_data_returned(self):
        """Ensure no demo data is ever returned"""
        parser = YClientsParser()
        result = parser.parse_url("https://invalid.example.com")
        assert result == []
        assert not any("Корт №" in str(item) for item in result)
    
    def test_background_scheduler_runs(self):
        """Test background scheduler functionality"""
        # Implementation...
    
    def test_duration_parsing(self):
        """Test duration extraction from various formats"""
        extractor = ProductionDataExtractor()
        test_cases = [
            ("60 мин", 60),
            ("1 час", 60),
            ("90 min", 90),
            ("1:30", 90),
        ]
        # Test implementation...
```

### **Integration Tests**
```python
# tests/test_integration_real.py
class TestRealIntegration:
    async def test_real_yclients_url(self):
        """Test with actual YClients URL"""
        if not os.getenv("TEST_REAL_URLS"):
            pytest.skip("Real URL testing disabled")
        
        url = "https://yclients.com/company/test/booking"
        parser = YClientsParser([url], db_manager)
        results = await parser.parse_all_urls()
        
        # Verify no demo data
        assert all("Нагатинская" not in str(data) for data in results.values())
```

### **Manual Testing Checklist**
- [ ] Start parser, verify no demo data in API responses
- [ ] Check background scheduling runs every 10 minutes
- [ ] Verify duration field contains real values (not hardcoded 60)
- [ ] Test with multiple YClients URLs
- [ ] Confirm Supabase saves contain real data only

---

## 📊 **Success Metrics**

### **Data Quality Metrics**
- **Demo Data**: 0% of responses contain fake tennis court data
- **Real Data**: >90% of valid URLs return genuine YClients data
- **Duration Accuracy**: >80% of records have non-default duration values
- **Price Validation**: <5% time-format values stored as prices

### **System Performance**
- **Background Scheduling**: 99% uptime for 10-minute intervals
- **Parse Success Rate**: >85% for valid YClients URLs
- **Database Saves**: >95% success rate for extracted data
- **Response Time**: <30 seconds average per URL

### **Monitoring & Alerting**
```python
# Add to parse_results for monitoring
parse_results.update({
    "demo_data_returned": False,
    "real_data_count": len(real_records),
    "background_scheduler_active": True,
    "last_successful_parse": datetime.now().isoformat(),
    "data_quality_score": calculate_quality_score(data)
})
```

---

## 🚀 **Deployment Plan**

### **Rollout Strategy**
1. **Phase 1**: Deploy demo data removal (low risk)
2. **Phase 2**: Enable background scheduling (medium risk)  
3. **Phase 3**: Activate duration parsing (low risk)
4. **Phase 4**: Enhance navigation (medium risk)
5. **Phase 5**: Full validation pipeline (low risk)

### **Rollback Plan**
- Keep original `lightweight_parser.py` as `lightweight_parser_backup.py`
- Environment flag to disable background scheduling if needed
- Database rollback scripts for schema changes

### **Monitoring**
- Dashboard for parse success rates
- Alerts for demo data detection
- Background scheduler health checks
- Data quality metrics tracking

---

*This specification provides the complete roadmap for transitioning from demo data to real YClients parsing with automatic scheduling and enhanced data quality.*