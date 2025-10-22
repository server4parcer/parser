#!/usr/bin/env python3
"""
YClients HTML Investigation Script
===================================
This script opens a real YClients booking page and analyzes the HTML structure
to identify the correct CSS selectors for price and provider extraction.

Purpose: Find why price/provider selectors are failing (100% fallback strings in DB)
"""

import asyncio
import re
from playwright.async_api import async_playwright
from datetime import datetime

# Test URLs
TEST_URLS = [
    "https://n1165596.yclients.com/company/1109937/record-type?o=",
    "https://b918666.yclients.com/company/855029/personal/menu?o=m-1",
]

async def investigate_yclients_html():
    """Inspect actual YClients page to find correct selectors."""

    print("=" * 80)
    print("🔍 YClients HTML Structure Investigation")
    print("=" * 80)
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Target: {TEST_URLS[0]}")
    print()

    async with async_playwright() as p:
        # Launch browser (non-headless to see what's happening)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("📄 Loading YClients page...")
        await page.goto(TEST_URLS[0], wait_until='networkidle', timeout=30000)
        print("✅ Page loaded")
        print()

        # Wait for booking content to load
        await page.wait_for_timeout(3000)

        # ========================================
        # STEP 1: Find all time slots/booking elements
        # ========================================
        print("-" * 80)
        print("STEP 1: Finding booking slot elements")
        print("-" * 80)

        # Try common slot selectors
        slot_selectors = [
            ".time-slot",
            ".booking-slot",
            ".schedule-item",
            ".slot",
            "[data-time]",
            ".available-time",
            "div[class*='slot']",
            "div[class*='time']",
        ]

        found_slots = []
        for selector in slot_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"✅ Found {len(elements)} elements with selector: {selector}")
                    found_slots.append((selector, elements))
                    if len(elements) > 0:
                        break  # Use first working selector
            except Exception as e:
                print(f"❌ Selector '{selector}' failed: {e}")

        if not found_slots:
            print("⚠️  No slot elements found! Dumping full page HTML...")
            page_html = await page.content()
            with open("/tmp/yclients_full_page.html", "w", encoding="utf-8") as f:
                f.write(page_html)
            print("📝 Full HTML saved to /tmp/yclients_full_page.html")
            print()
            print("🔍 Analyzing page structure...")

            # Get all divs with class containing booking-related keywords
            all_divs = await page.query_selector_all("div")
            print(f"Total divs on page: {len(all_divs)}")

            # Check for common booking UI patterns
            for keyword in ['time', 'slot', 'booking', 'schedule', 'available']:
                count = await page.evaluate(f'''
                    () => document.querySelectorAll('[class*="{keyword}"]').length
                ''')
                if count > 0:
                    print(f"  - Elements with '{keyword}' in class: {count}")

            await browser.close()
            return

        print()

        # Use first found slot selector
        slot_selector, slot_elements = found_slots[0]
        print(f"🎯 Using slot selector: {slot_selector}")
        print(f"📊 Total slots found: {len(slot_elements)}")
        print()

        # ========================================
        # STEP 2: Analyze first 3 slots in detail
        # ========================================
        print("-" * 80)
        print("STEP 2: Analyzing first 3 slots in detail")
        print("-" * 80)
        print()

        for i, slot in enumerate(slot_elements[:3], 1):
            print(f"📌 SLOT {i}:")
            print("-" * 40)

            # Get outer HTML
            outer_html = await slot.evaluate("el => el.outerHTML")
            print(f"HTML:\n{outer_html[:500]}...")
            print()

            # Get all text content
            text_content = await slot.evaluate("el => el.textContent")
            print(f"Text: {text_content.strip()}")
            print()

            # Get all child elements with classes
            children = await slot.query_selector_all("*")
            print(f"Child elements: {len(children)}")
            for child in children[:10]:  # First 10 children
                tag = await child.evaluate("el => el.tagName")
                classes = await child.evaluate("el => el.className")
                text = await child.evaluate("el => el.textContent")
                if classes and text.strip():
                    print(f"  - <{tag.lower()} class='{classes}'>{text.strip()[:50]}")
            print()

            # ========================================
            # STEP 3: Search for price patterns
            # ========================================
            print("  💰 PRICE ANALYSIS:")

            # Look for elements with currency symbols
            price_candidates = await slot.evaluate('''
                el => {
                    const candidates = [];
                    const all = el.querySelectorAll('*');
                    all.forEach(elem => {
                        const text = elem.textContent;
                        if (text && (text.includes('₽') || text.includes('руб') || /\\d+/.test(text))) {
                            candidates.push({
                                tag: elem.tagName,
                                class: elem.className,
                                id: elem.id,
                                text: text.trim(),
                                hasDataPrice: elem.hasAttribute('data-price'),
                                hasDataCost: elem.hasAttribute('data-cost')
                            });
                        }
                    });
                    return candidates;
                }
            ''')

            if price_candidates:
                print(f"  Found {len(price_candidates)} price candidates:")
                for pc in price_candidates[:5]:
                    print(f"    - <{pc['tag'].lower()} class='{pc['class']}'>{pc['text'][:50]}")
                    if pc['hasDataPrice']:
                        print(f"      ⚡ HAS data-price attribute!")
            else:
                print("  ❌ No price candidates found in this slot")
            print()

            # ========================================
            # STEP 4: Search for provider/staff patterns
            # ========================================
            print("  👤 PROVIDER/STAFF ANALYSIS:")

            # Look for Russian text (likely provider names)
            provider_candidates = await slot.evaluate('''
                el => {
                    const candidates = [];
                    const all = el.querySelectorAll('*');
                    all.forEach(elem => {
                        const text = elem.textContent.trim();
                        // Russian name pattern: starts with capital Cyrillic
                        if (text && /^[А-ЯЁ][а-яё]/.test(text) && text.length > 2) {
                            candidates.push({
                                tag: elem.tagName,
                                class: elem.className,
                                id: elem.id,
                                text: text,
                                hasDataStaff: elem.hasAttribute('data-staff') ||
                                             elem.hasAttribute('data-staff-name')
                            });
                        }
                    });
                    return candidates;
                }
            ''')

            if provider_candidates:
                print(f"  Found {len(provider_candidates)} provider candidates:")
                for pc in provider_candidates[:5]:
                    print(f"    - <{pc['tag'].lower()} class='{pc['class']}'>{pc['text'][:50]}")
                    if pc['hasDataStaff']:
                        print(f"      ⚡ HAS data-staff attribute!")
            else:
                print("  ❌ No provider candidates found in this slot")
            print()

            # ========================================
            # STEP 5: Search for time patterns
            # ========================================
            print("  🕐 TIME ANALYSIS:")

            time_candidates = await slot.evaluate('''
                el => {
                    const candidates = [];
                    const all = el.querySelectorAll('*');
                    all.forEach(elem => {
                        const text = elem.textContent.trim();
                        // Time pattern: HH:MM
                        if (text && /\\d{1,2}:\\d{2}/.test(text)) {
                            candidates.push({
                                tag: elem.tagName,
                                class: elem.className,
                                id: elem.id,
                                text: text,
                                hasDataTime: elem.hasAttribute('data-time')
                            });
                        }
                    });
                    return candidates;
                }
            ''')

            if time_candidates:
                print(f"  Found {len(time_candidates)} time candidates:")
                for tc in time_candidates[:5]:
                    print(f"    - <{tc['tag'].lower()} class='{tc['class']}'>{tc['text'][:50]}")
                    if tc['hasDataTime']:
                        print(f"      ⚡ HAS data-time attribute!")
            else:
                print("  ❌ No time candidates found in this slot")

            print()
            print("=" * 80)
            print()

        # ========================================
        # STEP 6: Summary & Recommendations
        # ========================================
        print("-" * 80)
        print("STEP 6: SUMMARY & RECOMMENDATIONS")
        print("-" * 80)
        print()

        print("📋 Next Steps:")
        print("1. Review the HTML structure above")
        print("2. Identify the ACTUAL class names used for:")
        print("   - Price elements (look for ₽ or руб)")
        print("   - Provider/staff names (look for Russian names)")
        print("   - Time elements (look for HH:MM patterns)")
        print()
        print("3. Update yclients_real_selectors.py with correct selectors")
        print("4. Test extraction with updated selectors")
        print()

        print("💾 Full page HTML saved to /tmp/yclients_full_page.html")
        page_html = await page.content()
        with open("/tmp/yclients_full_page.html", "w", encoding="utf-8") as f:
            f.write(page_html)

        print()
        print("⏸️  Browser will stay open for 30 seconds for manual inspection...")
        print("   Use DevTools (F12) to inspect elements manually")
        await page.wait_for_timeout(30000)

        await browser.close()
        print("✅ Investigation complete!")

if __name__ == "__main__":
    asyncio.run(investigate_yclients_html())
