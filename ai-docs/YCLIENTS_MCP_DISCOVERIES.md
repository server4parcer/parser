# YClients MCP Playwright Discoveries

**Critical Findings from Browser Automation Investigation**  
*This document contains the REAL YClients structure discovered via MCP Playwright*

---

## 🚨 **MASSIVE DISCOVERY: Demo Data Was Real!**

The "demo data" in our system (Нагатинская, Корт №1 Ультрапанорамик, etc.) is **ACTUAL REAL DATA** from Pavel's venue! This wasn't fake data - it was real court names from the actual YClients booking system.

---

## 🔍 **YClients 4-Step Navigation Flow**

### **Complete User Journey to Reach Prices**

```
1. Service Type Selection (record-type?o=)
   ↓ Click service type (e.g., "Индивидуальные услуги")
2. Court/Master Selection (personal/select-master) 
   ↓ Click specific court (e.g., "Корт №1 Ультрапанорамик")
3. Date & Time Selection (personal/select-time)
   ↓ Select date, then click time slot (e.g., "15:00")
4. Service Package Selection (personal/select-services)
   ↓ PRICES APPEAR HERE!
```

**Critical Insight**: Prices are NOT available until step 4! This is why simple HTML parsing fails.

---

## 📍 **Real Venue Data Structure**

### **Actual Venue: Нагатинская**
```json
{
  "location": "Нагатинская",
  "courts": [
    {
      "name": "Корт №1 Ультрапанорамик",
      "id": "m3451630",
      "services": [
        {
          "name": "Ультрапанорамик 1 час БУДНИЙ",
          "price": "6,000 ₽",
          "duration": "1 ч",
          "prepayment": "100% предоплата"
        },
        {
          "name": "Ультрапанорамик 1,5 часа БУДНИЙ",
          "price": "9,000 ₽",
          "duration": "1 ч 30 мин",
          "prepayment": "100% предоплата"
        },
        {
          "name": "Ультрапанорамик 2 часа БУДНИЙ",
          "price": "12,000 ₽",
          "duration": "2 ч",
          "prepayment": "100% предоплата"
        }
      ]
    },
    {
      "name": "Корт №2 Панорамик",
      "id": "m3451631"
    },
    {
      "name": "Корт №3 Панорамик",
      "id": "m3451632"
    }
  ]
}
```

---

## 🎯 **Real YClients Selectors**

### **Custom UI Kit Elements (Not Standard HTML!)**

```javascript
// YClients uses custom web components
'ui-kit-simple-cell'     // Container for services/courts
'ui-kit-headline'         // Service/court names
'ui-kit-title'           // Prices
'ui-kit-body'            // Duration and additional info
'ui-kit-button'          // Action buttons

// Navigation elements
'[role="link"]'          // Service type links
'[role="button"]'        // Continue buttons
'.calendar-day'          // Date selection
'.time-slot'             // Time selection (may vary)
```

### **Specific Selectors by Page**

#### **Step 1: Service Selection Page**
```javascript
// Service types
await page.getByRole('link', { name: 'Индивидуальные услуги' })
await page.getByRole('link', { name: 'Сплит бронирование' })
```

#### **Step 2: Court Selection Page**
```javascript
// Courts
await page.locator('ui-kit-simple-cell').filter({ hasText: 'Корт №1' })
await page.locator('ui-kit-simple-cell').filter({ hasText: 'Корт №2' })
// Continue button
await page.getByRole('button', { name: 'Продолжить' })
```

#### **Step 3: Date/Time Selection Page**
```javascript
// Calendar dates
await page.getByText('5', { exact: true }).nth(1)  // 5th day of month
// Time slots
await page.getByText('15:00')
await page.getByText('15:30')
// Continue button
await page.getByRole('button', { name: 'Продолжить' })
```

#### **Step 4: Service Package Page (PRICES HERE!)**
```javascript
// Service packages with prices
const services = await page.locator('ui-kit-simple-cell').all()
for (const service of services) {
  const name = await service.locator('ui-kit-headline').textContent()
  const price = await service.locator('ui-kit-title').textContent()
  const duration = await service.locator('ui-kit-body').textContent()
}
```

---

## 🔄 **URL Pattern Evolution**

### **How URL Changes Through Navigation**

```
1. Initial: 
   https://n1165596.yclients.com/company/1109937/record-type?o=

2. After service selection:
   https://n1165596.yclients.com/company/1109937/personal/select-master?o=s2801089

3. After court selection:
   https://n1165596.yclients.com/company/1109937/personal/select-time?o=s2801089m3451630

4. After time selection:
   https://n1165596.yclients.com/company/1109937/personal/select-services?o=s2801089m3451630d2511081500

URL Parameters:
- s2801089: Service ID
- m3451630: Master/Court ID  
- d2511081500: Date/Time (25/11/08 15:00)
```

---

## 💡 **Why BeautifulSoup/Requests Fails**

### **JavaScript Rendering Requirements**

1. **Initial HTML is empty shell** - Only contains React/Vue app container
2. **All content loads via JavaScript** - No static HTML data
3. **Multi-step navigation required** - Can't direct access price page
4. **Custom web components** - Not standard HTML elements
5. **Session state management** - Each step builds on previous

### **What We Saw with Requests**
```python
# BeautifulSoup sees this:
{
  "javascript": 1173 bytes,
  "html_content": 0 bytes,
  "time_slots": [],
  "prices": []
}
```

### **What Playwright Sees After JS Execution**
```python
# After JavaScript renders:
{
  "courts": ["Корт №1", "Корт №2", "Корт №3"],
  "time_slots": ["15:00", "15:30", "16:00", ...],
  "prices": ["6,000 ₽", "9,000 ₽", "12,000 ₽"],
  "durations": ["1 ч", "1 ч 30 мин", "2 ч"]
}
```

---

## 🎬 **Required Actions for Implementation**

### **Playwright Navigation Sequence**

```python
async def parse_yclients_booking(page, url):
    # Step 1: Load initial page
    await page.goto(url)
    await page.wait_for_selector('ui-kit-simple-cell')
    
    # Step 2: Select service type
    await page.get_by_role('link', { 'name': 'Индивидуальные услуги' }).click()
    await page.wait_for_url('**/personal/select-master**')
    
    # Step 3: Select court
    courts = await page.locator('ui-kit-simple-cell').all()
    for court in courts:
        court_name = await court.locator('ui-kit-headline').text_content()
        await court.click()
        
        # Step 4: Select date
        await page.wait_for_selector('.calendar-day')
        dates = await page.locator('.calendar-day.available').all()
        for date in dates:
            await date.click()
            
            # Step 5: Select time
            times = await page.locator('[data-time]').all()
            for time in times:
                await time.click()
                await page.get_by_role('button', { 'name': 'Продолжить' }).click()
                
                # Step 6: Extract prices (FINALLY!)
                await page.wait_for_selector('ui-kit-simple-cell')
                services = await extract_service_prices(page)
                
                # Navigate back for next slot
                await page.go_back()
```

---

## 🚫 **Common Pitfalls to Avoid**

1. **Don't try to skip steps** - Direct URLs to price pages don't work
2. **Don't use static selectors** - Elements change based on venue
3. **Don't ignore wait conditions** - Each step loads dynamically
4. **Don't parse initial HTML** - It's always empty
5. **Don't cache aggressively** - Availability changes in real-time

---

## ✅ **Validation Checklist**

- [ ] Can navigate through all 4 steps
- [ ] Extracts real court names (not generic)
- [ ] Gets actual prices in rubles
- [ ] Captures duration correctly
- [ ] Handles multiple courts per venue
- [ ] Works with different service types
- [ ] Manages session state properly
- [ ] No hardcoded demo data fallbacks

---

**🔑 Key Takeaway**: YClients is a complex SPA requiring full browser automation with multi-step navigation. BeautifulSoup/Requests will NEVER work for this system. Must use Playwright or similar browser automation tool.