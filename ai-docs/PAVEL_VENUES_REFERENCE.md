# Pavel's YClients Venues Reference

**AI Agent Memory Document**  
*Real venue URLs and characteristics for YClients parser development*

---

## 🏟️ **Pavel's Venue Portfolio**

### **1. Корты-Сетки (Tennis Courts)**
- **URL**: `https://n1308467.yclients.com/company/1192304/record-type?o=`
- **Type**: Service Selection Page (`record-type`)
- **Sport**: Tennis
- **Expected Data**: Court bookings, hourly slots, tennis-specific pricing

### **2. Multi-Location Club**
- **URL**: `https://b911781.yclients.com/select-city/2/select-branch?o=`
- **Type**: Location Selection (3 branches)
- **Special**: Requires branch selection before booking
- **Navigation**: City → Branch → Services → Booking

### **3. Working Reference Venue**
- **URL**: `https://n1165596.yclients.com/company/1109937/record-type?o=`
- **Type**: Service Selection Page
- **Status**: ✅ Currently functional (Pavel confirmed)
- **Use**: Primary testing and validation URL

### **4. Padel Friends**
- **URL**: `https://b861100.yclients.com/company/804153/personal/select-time?o=m-1`
- **Type**: Direct Booking Page (`personal/select-time`)
- **Sport**: Padel
- **Navigation**: Direct to time slot selection

### **5. ТК "Ракетлон" (Tennis Club Raketion)**
- **URL**: `https://b1009933.yclients.com/company/936902/personal/select-time?o=`
- **Type**: Direct Booking Page
- **Sport**: Tennis
- **Language**: Russian naming convention

### **6. Padel A33**
- **URL**: `https://b918666.yclients.com/company/855029/personal/menu?o=m-1`
- **Type**: Menu Page (`personal/menu`)
- **Sport**: Padel
- **Navigation**: Menu-based selection flow

---

## 🔍 **URL Pattern Analysis**

### **Service Selection Pattern**
```
https://{subdomain}.yclients.com/company/{id}/record-type?o=
```
**Characteristics**:
- Requires service selection first
- Shows available services/courts
- User must click to proceed to booking

### **Direct Booking Pattern**
```
https://{subdomain}.yclients.com/company/{id}/personal/select-time?o={params}
```
**Characteristics**:
- Direct access to time slot selection
- Calendar and available times visible immediately
- Faster booking flow

### **Menu Pattern**
```
https://{subdomain}.yclients.com/company/{id}/personal/menu?o={params}
```
**Characteristics**:
- Menu-driven navigation
- Multiple service options
- May require multiple clicks to reach booking

### **Multi-Location Pattern**
```
https://{subdomain}.yclients.com/select-city/{id}/select-branch?o=
```
**Characteristics**:
- Geographic selection required
- Multiple venue locations
- Complex navigation flow

---

## 🎾 **Sport Type Mapping**

### **Tennis Venues**
- **Корты-Сетки**: Traditional tennis courts
- **ТК "Ракетлон"**: Tennis club with Russian branding
- **Expected Data**: Court numbers, indoor/outdoor, surface type

### **Padel Venues**
- **Padel Friends**: Modern padel facility
- **Padel A33**: Specialized padel courts
- **Expected Data**: Padel-specific court sizes, player count (4-person booking)

### **Mixed/Unknown**
- **Working Reference**: Unknown sport type - need investigation
- **Multi-Location**: Multiple sports possible

---

## 🔧 **Technical Characteristics**

### **URL Structure Insights**
```
Subdomain Patterns:
- n1308467.yclients.com (numeric prefix 'n')
- b911781.yclients.com  (numeric prefix 'b')
- Pattern: {letter}{numbers}.yclients.com
```

### **Company ID Patterns**
```
Company IDs:
1192304, 1109937, 804153, 936902, 855029
Range: 6-7 digits
Pattern: Incremental assignment
```

### **Parameter Patterns**
```
?o=           (empty parameter)
?o=m-1        (master/staff selection?)
```

---

## 🚨 **Parser Implications**

### **Multi-Flow Handling Required**
The parser must handle 4 different navigation flows:
1. **Service Selection** → Click service → Get booking page
2. **Direct Booking** → Calendar interaction → Time slots
3. **Menu Navigation** → Menu selection → Booking flow
4. **Multi-Location** → City → Branch → Service → Booking

### **Dynamic Content Expectations**
- **AJAX Loading**: Time slots load after date selection
- **User Interaction**: Clicks required for full data access
- **Wait Conditions**: Content may load progressively

### **Data Extraction Complexity**
- **Sport-Specific**: Tennis courts vs Padel courts have different layouts
- **Language Variants**: Russian vs English venue names
- **Pricing Variations**: Different sports have different pricing structures

---

## 🎯 **Investigation Strategy**

### **Phase 1: Functional Validation**
Start with: `https://n1165596.yclients.com/company/1109937/record-type?o=`
- Confirmed working by Pavel
- Service selection flow
- Establish baseline understanding

### **Phase 2: Pattern Recognition**
Test each URL type:
- Document navigation requirements
- Map selector patterns
- Identify common elements

### **Phase 3: Sport-Specific Adaptation**
- Tennis-specific data extraction
- Padel-specific booking patterns
- Multi-sport venue handling

---

## 📊 **Expected Real Data Samples**

### **Tennis Venue (Корты-Сетки)**
```json
{
  "venue_name": "Корты-Сетки",
  "court_type": "TENNIS",
  "time": "10:00",
  "price": "2000 ₽",
  "duration": 60,
  "court_number": "Корт №1",
  "surface_type": "Hard court"
}
```

### **Padel Venue (Padel Friends)**
```json
{
  "venue_name": "Padel Friends", 
  "court_type": "PADEL",
  "time": "18:00",
  "price": "3200 ₽",
  "duration": 90,
  "players": 4,
  "court_name": "Court A"
}
```

---

**🔍 Context for AI Agents**: These are Pavel's real business venues. All parsing must extract genuine data from these URLs. No demo data fallbacks allowed - if parsing fails, return empty results and log the specific failure for debugging.