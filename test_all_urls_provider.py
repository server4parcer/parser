#!/usr/bin/env python3
"""
Test provider field capture across ALL production URLs.
This simulates what the production cron will do.
"""
import asyncio
import sys
import os

sys.path.insert(0, '/Users/m/git/clients/yclents/yclients-local-fix')

from src.database.db_manager import DatabaseManager
from src.parser.yclients_parser import YClientsParser

# All production URLs
PRODUCTION_URLS = [
    'https://n1308467.yclients.com/company/1192304/record-type?o=',
    'https://b911781.yclients.com/select-city/2/select-branch?o=',
    'https://n1165596.yclients.com/company/1109937/record-type?o=',
    'https://b861100.yclients.com/company/804153/personal/select-time?o=m-1',
    'https://b1009933.yclients.com/company/936902/personal/select-time?o=',
    'https://b918666.yclients.com/company/855029/personal/menu?o=m-1'
]

async def test_all_urls():
    """Test provider capture for all production URLs"""

    print("="*80)
    print("TESTING PROVIDER FIELD ACROSS ALL PRODUCTION URLS")
    print("="*80)
    print(f"\nTotal URLs to test: {len(PRODUCTION_URLS)}")
    print()

    # Initialize database
    print("1. Initializing database connection...")
    db = DatabaseManager()
    await db.initialize()
    print("   ✅ Database connected\n")

    results_summary = []

    for idx, url in enumerate(PRODUCTION_URLS, 1):
        print(f"\n{'='*80}")
        print(f"URL {idx}/{len(PRODUCTION_URLS)}: {url[:70]}...")
        print('='*80)

        try:
            # Initialize parser for this URL
            parser = YClientsParser([url], db)
            await parser.initialize()

            # Parse URL (timeout after 2 minutes)
            print(f"⏳ Parsing (max 2 minutes)...")
            success, data = await parser.parse_url(url)

            # Close parser
            await parser.close()

            if not success or not data:
                print(f"⚠️  No data extracted from this URL")
                results_summary.append({
                    'url': url,
                    'status': 'NO_DATA',
                    'provider': None,
                    'records': 0
                })
                continue

            # Analyze provider field
            providers_found = []
            unknown_count = 0

            for record in data:
                provider = record.get('provider', 'Unknown')
                if provider == 'Unknown':
                    unknown_count += 1
                elif provider not in providers_found:
                    providers_found.append(provider)

            # Summary for this URL
            print(f"\n📊 Results:")
            print(f"   Records extracted: {len(data)}")
            print(f"   Unique providers: {len(providers_found)}")
            print(f"   'Unknown' count: {unknown_count}")

            if providers_found:
                print(f"\n   Providers found:")
                for p in providers_found[:3]:
                    print(f"   - {p}")
                if len(providers_found) > 3:
                    print(f"   ... and {len(providers_found) - 3} more")

            # Save to Supabase
            print(f"\n💾 Saving to Supabase...")
            await db.save_booking_data(url, data)
            print(f"   ✅ Saved {len(data)} records")

            # Determine status
            if unknown_count == len(data):
                status = 'ALL_UNKNOWN'
            elif unknown_count > 0:
                status = 'PARTIAL'
            else:
                status = 'SUCCESS'

            results_summary.append({
                'url': url,
                'status': status,
                'provider': providers_found[0] if providers_found else 'Unknown',
                'records': len(data),
                'unknown_count': unknown_count
            })

        except Exception as e:
            print(f"\n❌ Error: {e}")
            results_summary.append({
                'url': url,
                'status': 'ERROR',
                'provider': None,
                'records': 0,
                'error': str(e)
            })

    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print()

    success_count = sum(1 for r in results_summary if r['status'] == 'SUCCESS')
    partial_count = sum(1 for r in results_summary if r['status'] == 'PARTIAL')
    failed_count = sum(1 for r in results_summary if r['status'] in ['ALL_UNKNOWN', 'NO_DATA', 'ERROR'])

    print(f"✅ Success (providers captured): {success_count}/{len(PRODUCTION_URLS)}")
    print(f"⚠️  Partial (some Unknown): {partial_count}/{len(PRODUCTION_URLS)}")
    print(f"❌ Failed (no providers): {failed_count}/{len(PRODUCTION_URLS)}")
    print()

    print("Details:")
    print("-" * 80)
    for r in results_summary:
        status_icon = {
            'SUCCESS': '✅',
            'PARTIAL': '⚠️',
            'ALL_UNKNOWN': '❌',
            'NO_DATA': '⚠️',
            'ERROR': '❌'
        }.get(r['status'], '?')

        url_short = r['url'][:60] + "..." if len(r['url']) > 60 else r['url']
        provider_display = r['provider'][:40] if r['provider'] else 'None'

        print(f"{status_icon} {url_short}")
        print(f"   Provider: {provider_display} | Records: {r['records']}")
        if r.get('unknown_count', 0) > 0:
            print(f"   Unknown count: {r['unknown_count']}")
        print()

    await db.close()

    # Exit code
    if success_count + partial_count == len(PRODUCTION_URLS):
        print("🎉 TEST PASSED: Provider field is being captured!")
        sys.exit(0)
    else:
        print("⚠️  TEST PARTIAL: Some URLs failed to capture providers")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(test_all_urls())
