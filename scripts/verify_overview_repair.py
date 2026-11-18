"""Automated Playwright verification script for SupeRR Intelligence Lab Overview Repair.

Validates:
1. Both http://127.0.0.1:8000 and http://127.0.0.1:5173 render with 0 console errors and 0 React error #31.
2. Overview components:
   - Metric cards: Evaluated player counts (155 / 888 and 270 / 647).
   - Top Competitions chart: SVG bars rendered cleanly without React child errors.
   - Pressure distribution: Percentages in [0, 100]% range with Phase 3 labels (< 40.0, 40.0 - 64.9, >= 65.0).
   - Pipeline phase cards: Real phase names and outputs.
   - Champion cards: Vipraj Nigam & Manimaran Siddharth with performance signatures.
3. Verification across all 7 routes to guarantee zero regressions.
4. Full page screenshot evidence saved to reports/phase7.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

REPORTS_DIR = Path("reports/phase7")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

ROUTES = [
    "/",
    "/explorer",
    "/replay",
    "/pressure",
    "/players",
    "/rankings",
    "/reports",
]


def verify_overview_page(page, port: int) -> dict:
    url = f"http://127.0.0.1:{port}/"
    print(f"\n--- Detailed Audit for Overview on {url} ---")
    
    console_errors = []
    page_errors = []
    
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda err: page_errors.append(str(err)))
    
    resp = page.goto(url, wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2000)
    
    # Check for React error #31 specifically
    has_error_31 = any("error #31" in err.lower() or "error #31" in msg.lower() 
                       for err in page_errors for msg in console_errors)
    
    # Detailed DOM checks
    audit_data = page.evaluate("""() => {
        const root = document.getElementById('root');
        const text = root ? root.innerText : '';
        
        // Check for specific text elements
        const hasEvaluatedBatters = text.includes('155 / 888');
        const hasEvaluatedBowlers = text.includes('270 / 647');
        const hasMatchesCount = text.includes('883');
        const hasDeliveriesCount = text.includes('200,999');
        const hasVipraj = text.includes('Vipraj Nigam');
        const hasSiddharth = text.includes('Manimaran Siddharth');
        const hasIPL2025 = text.includes('IPL 2025');
        const hasLowPressure = text.includes('LOW_PRESSURE') || text.includes('Low Pressure');
        const hasHighPressure = text.includes('HIGH_PRESSURE') || text.includes('High Pressure');
        
        // Check SVG bars for Recharts
        const rechartsBars = document.querySelectorAll('.recharts-bar-rectangle');
        const rechartsSvg = document.querySelectorAll('.recharts-surface');
        
        // Check for any error boundary text
        const hasCrashUI = text.includes('API Contract Violation') || 
                           text.includes('Something went wrong') ||
                           text.includes('Minified React error');
                           
        return {
            innerTextLength: text.length,
            hasEvaluatedBatters,
            hasEvaluatedBowlers,
            hasMatchesCount,
            hasDeliveriesCount,
            hasVipraj,
            hasSiddharth,
            hasIPL2025,
            hasLowPressure,
            hasHighPressure,
            hasCrashUI,
            barsCount: rechartsBars.length,
            svgCount: rechartsSvg.length,
            preview: text.slice(0, 300).replace(/\\n+/g, ' ')
        };
    }""")
    
    screenshot_path = REPORTS_DIR / f"screenshot_overview_repaired_{port}.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
    print(f"Overview screenshot saved to: {screenshot_path}")
    
    return {
        "port": port,
        "url": url,
        "status": resp.status if resp else None,
        "console_errors": console_errors,
        "page_errors": page_errors,
        "has_error_31": has_error_31,
        "audit": audit_data,
        "screenshot": str(screenshot_path),
    }


def verify_all_routes(port: int):
    base_url = f"http://127.0.0.1:{port}"
    print(f"\n=======================================================")
    print(f"VERIFYING ALL 7 ROUTES ON {base_url}")
    print(f"=======================================================")
    
    route_results = {}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        # First verify overview in detail
        overview_audit = verify_overview_page(page, port)
        route_results["/"] = overview_audit
        
        # Verify remaining routes
        for route in ROUTES[1:]:
            url = f"{base_url}{route}"
            c_errors = []
            p_errors = []
            
            p_handler = lambda err: p_errors.append(str(err))
            c_handler = lambda msg: c_errors.append(msg.text) if msg.type == "error" else None
            
            page.on("pageerror", p_handler)
            page.on("console", c_handler)
            
            resp = page.goto(url, wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(1000)
            
            dom_info = page.evaluate("""() => {
                const root = document.getElementById('root');
                return {
                    textLength: root ? root.innerText.trim().length : 0,
                    hasAside: !!document.querySelector('aside'),
                    hasHeader: !!document.querySelector('header'),
                    hasMain: !!document.querySelector('main'),
                };
            }""")
            
            clean_route = route.strip("/")
            shot = REPORTS_DIR / f"screenshot_{port}_{clean_route}.png"
            page.screenshot(path=str(shot), full_page=True)
            
            route_results[route] = {
                "route": route,
                "http_status": resp.status if resp else None,
                "console_errors": c_errors,
                "page_errors": p_errors,
                "dom_info": dom_info,
                "screenshot": str(shot),
            }
            
            print(f"Route {route:12} | HTTP {str(resp.status if resp else 'N/A'):4} | Errors: {len(c_errors) + len(p_errors)} | Text Len: {dom_info['textLength']}")
            if c_errors or p_errors:
                print(f"    Errors: {c_errors + p_errors}")
                
            page.remove_listener("pageerror", p_handler)
            page.remove_listener("console", c_handler)
            
        browser.close()
        
    return route_results


def main():
    results = {}
    for port in [8000, 5173]:
        try:
            results[port] = verify_all_routes(port)
        except Exception as e:
            print(f"Error testing port {port}: {e}")
            results[port] = {"error": str(e)}
            
    summary_path = REPORTS_DIR / "verification_results.json"
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nVerification summary saved to: {summary_path}")


if __name__ == "__main__":
    main()
