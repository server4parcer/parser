#!/usr/bin/env python3
"""
Test ALL 6 production URLs from TimeWeb environment.
Find which one successfully extracts data with prices.
"""
import asyncio
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.database.db_manager import DatabaseManager
from src.parser.yclients_parser import YClientsParser

# The 6 production URLs from TimeWeb PARSE_URLS environment variable
PRODUCTION_URLS = [
    "https://n1165596.yclients.com/company/1109937/record-type?o=",  # Нагатинская
    "https://n1308467.yclients.com/company/1192304/record-type?o=",  # Корты-Сетки
    "https://b861100.yclients.com/company/804153/personal/select-time?o=m-1",  # Padel Friends
    "https://b1009933.yclients.com/company/936902/personal/select-time?o=",  # ТК Ракетлон
    "https://b918666.yclients.com/company/855029/personal/menu?o=m-1",  # Padel A33
]

async def test_url(url: str, db_manager: DatabaseManager):
    """Test a single URL and return results"""
    print(f"\n{'='*80}")
    print(f"Testing: {url}")
    print(f"{'='*80}")

    parser = YClientsParser([url], db_manager)
    await parser.initialize()

    success, data = await parser.parse_url(url)

    await parser.close()

    return {
        'url': url,
        'success': success,
        'records': len(data),
        'has_prices': any(r.get('price') and r.get('price') != 'None' for r in data) if data else False,
        'has_providers': any(r.get('provider') and r.get('provider') != 'None' for r in data) if data else False,
        'sample': data[0] if data else None
    }

async def main():
    print("🚀 Testing ALL 5 Production URLs")
    print("Goal: Find which URLs extract complete data (dates, times, prices, providers)")

    db_manager = DatabaseManager()
    await db_manager.initialize()
    print("✅ Database connected\n")

    results = []
    for url in PRODUCTION_URLS:
        try:
            result = await test_url(url, db_manager)
            results.append(result)

            print(f"\n📊 Result:")
            print(f"   Success: {result['success']}")
            print(f"   Records: {result['records']}")
            print(f"   Has Prices: {result['has_prices']}")
            print(f"   Has Providers: {result['has_providers']}")

            if result['sample']:
                print(f"\n   Sample Record:")
                sample = result['sample']
                print(f"      date: {sample.get('date')}")
                print(f"      time: {sample.get('time')}")
                print(f"      price: {sample.get('price')}")
                print(f"      provider: {sample.get('provider')}")

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                'url': url,
                'success': False,
                'records': 0,
                'error': str(e)
            })

    await db_manager.close()

    print(f"\n\n{'='*80}")
    print("📋 SUMMARY OF ALL TESTS")
    print(f"{'='*80}\n")

    for i, result in enumerate(results, 1):
        status = "✅ COMPLETE" if result.get('has_prices') and result.get('has_providers') else \
                 "⚠️  PARTIAL" if result['records'] > 0 else \
                 "❌ FAILED"

        print(f"{i}. {status}")
        print(f"   URL: {result['url'][:60]}...")
        print(f"   Records: {result['records']}, Prices: {result.get('has_prices')}, Providers: {result.get('has_providers')}")
        print()

    # Find the best URL
    complete_urls = [r for r in results if r.get('has_prices') and r.get('has_providers')]
    if complete_urls:
        print(f"🎯 WINNER: {len(complete_urls)} URL(s) extracted COMPLETE data!")
        for r in complete_urls:
            print(f"   ✅ {r['url']}")
    else:
        partial_urls = [r for r in results if r['records'] > 0]
        if partial_urls:
            print(f"⚠️  {len(partial_urls)} URL(s) extracted PARTIAL data (dates/times only)")
            print("   Need to fix price/provider extraction")
        else:
            print("❌ NO URLs extracted any data - major issue!")

if __name__ == "__main__":
    asyncio.run(main())
