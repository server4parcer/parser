# 🚀 MANUAL DEPLOYMENT INSTRUCTIONS

## SITUATION
- ✅ **Local parser**: Working perfectly, captures real prices (2800.0, 5000.0, 4500.0, 6000.0)
- ❌ **Production parser**: Still returning fallback values ("Цена не найдена", "Не указан")
- 🚫 **GitHub access**: Permission denied for auto-deployment

## ROOT CAUSE
Production version is using DOM scraping fallback instead of API capture mode. The API capture is implemented and working locally, but production falls back to HTML parsing.

## MANUAL DEPLOYMENT STEPS

### Option 1: Direct File Upload (Recommended)
1. **Access TimeWeb VDS** via SSH or file manager
2. **Navigate to**: `/home/yclients-parser/` or deployment directory
3. **Replace these files**:
   ```
   src/parser/yclients_parser.py         # Updated with API capture
   src/parser/production_data_extractor.py # Fixed fallback logic
   src/main.py                           # Updated parser logic
   ```

### Option 2: TimeWeb Web Interface
1. **Log in** to TimeWeb control panel
2. **Find** the YClients parser application
3. **Upload** the entire `src/` directory
4. **Restart** the application

### Option 3: Git Repository Fix
1. **Contact Pavel** to fix GitHub permissions
2. **Or** add SSH key to TimeWeb VDS
3. Then run: `git pull origin main`

## CRITICAL CHANGES NEEDED

### File: `src/parser/yclients_parser.py`
- **Lines 161-165**: API capture is working ✅
- **Lines 200-220**: API extraction logic implemented ✅
- **Lines 300-350**: Fallback logic needs optimization

### File: `src/parser/production_data_extractor.py`
- **Line 300**: Change fallback from `"Цена не найдена"` to actual price extraction
- **Lines 294-296**: Improve time detection logic

## TESTING PRODUCTION FIX

After deployment, test with:
```bash
curl -s "https://server4parcer-parser-4949.twc1.net/data?api_key=yclients_parser_secure_key_2024&limit=3" | python -m json.tool
```

**Expected result**: Real prices like `"2800₽"`, `"5000₽"` instead of `"Цена не найдена"`

## LOCAL VERIFICATION SCRIPT
Run this to confirm fix works:
```bash
source venv/bin/activate && export SUPABASE_URL=... && export SUPABASE_KEY=... && python -c "
import asyncio
from src.parser.yclients_parser import YClientsParser
from src.database.db_manager import DatabaseManager

async def test():
    db = DatabaseManager()
    await db.initialize()
    parser = YClientsParser(['https://n1165596.yclients.com/company/1109937/record-type?o='], db)
    await parser.initialize()
    success, data = await parser.parse_url('https://n1165596.yclients.com/company/1109937/record-type?o=')
    print(f'Success: {success}, Records: {len(data)}')
    for record in data[:2]:
        print(f'Price: {record.get(\"price\", \"N/A\")}, Provider: {record.get(\"provider\", \"N/A\")}')
    await parser.close()
    await db.close()

asyncio.run(test())
"
```

## CONTACT PAVEL
Send this message:
> "Pavel, the YClients parser is working locally and capturing real API data with prices like 2800.0, 5000.0, etc. However production is still showing fallback values. I need manual deployment to update the production server with the fixed API capture logic. Can you either fix GitHub permissions or help deploy the updated files?"

## SUCCESS CRITERIA
- Local: ✅ Working (real prices captured)
- Production: ❌ Needs fix (fallback values showing)
- GitHub: 🚫 Blocked (need permissions fix)