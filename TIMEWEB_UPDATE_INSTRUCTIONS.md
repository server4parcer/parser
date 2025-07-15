
# 🚀 TIMEWEB MULTI-URL UPDATE INSTRUCTIONS

## Step 1: Access TimeWeb Dashboard
1. Open: https://timeweb.cloud/my/cloud-apps
2. Find: YC-parser application
3. Click: "Settings" or "Настройки"

## Step 2: Update Environment Variables
1. Go to: Environment Variables section
2. Find: PARSE_URLS variable
3. Click: Edit/Редактировать

## Step 3: Replace URL Value
**Current value:** Single URL
**New value:** Copy the entire line below (all 6 URLs):

https://n1308467.yclients.com/company/1192304/record-type?o=,https://b911781.yclients.com/select-city/2/select-branch?o=,https://n1165596.yclients.com/company/1109937/record-type?o=,https://b861100.yclients.com/company/804153/personal/select-time?o=m-1,https://b1009933.yclients.com/company/936902/personal/select-time?o=,https://b918666.yclients.com/company/855029/personal/menu?o=m-1

## Step 4: Save and Deploy
1. Click: Save/Сохранить
2. Wait: 2-3 minutes for automatic restart
3. Check: Application logs for restart confirmation

## Step 5: Verify Multi-URL Deployment
1. Test: https://server4parcer-parser-4949.twc1.net/api/urls
2. Should show: 6 URLs configured
3. Run parser: POST /parser/run
4. Check data: GET /api/booking-data

## Expected Results After Update:
- ✅ 6 URLs configured (vs 1 currently)
- ✅ ~30 records extracted (vs 3 currently)  
- ✅ 6 venues covered (vs 1 currently)
- ✅ All venues: Корты-Сетки, Lunda Padel, Нагатинская, Padel Friends, ТК "Ракетлон", Padel A33

## Rollback Plan (if issues):
Replace PARSE_URLS with original single URL:
https://n1165596.yclients.com/company/1109937/record-type?o=
