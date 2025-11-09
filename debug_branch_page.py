#!/usr/bin/env python3
"""
Debug script to see what's actually on the branch selection page.
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_branch_page():
    url = "https://b911781.yclients.com/select-city/2/select-branch?o="

    print(f"🔍 Loading: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Non-headless to see what's happening
        page = await browser.new_page()

        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(3000)  # Wait for page to fully load

        print(f"\n📄 Page title: {await page.title()}")
        print(f"📍 Current URL: {page.url}")

        # Try various selectors for branch links
        selectors_to_try = [
            'ui-kit-simple-cell',
            'a[href*="/company/"]',
            'a[href*="record"]',
            '.branch-link',
            '[class*="location"]',
            'button',
            'a',
            'div[role="button"]',
        ]

        for selector in selectors_to_try:
            try:
                elements = await page.locator(selector).all()
                if elements:
                    print(f"\n✅ Found {len(elements)} elements with selector: {selector}")
                    for i, el in enumerate(elements[:5]):  # First 5 only
                        text = await el.text_content()
                        html = await el.evaluate('el => el.outerHTML')
                        print(f"   {i+1}. Text: {text[:100]}")
                        print(f"      HTML: {html[:200]}")
            except Exception as e:
                print(f"\n❌ Selector '{selector}' failed: {e}")

        # Get page HTML snippet
        html_snippet = await page.content()
        print(f"\n📋 Page HTML (first 2000 chars):")
        print(html_snippet[:2000])

        input("\nPress Enter to close browser...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_branch_page())
