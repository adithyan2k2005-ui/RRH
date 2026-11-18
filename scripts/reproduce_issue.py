"""Reproduction script using Playwright to diagnose root rendering failure on both ports."""

import json
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

REPORTS_DIR = Path("reports/phase7")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def test_url(url: str, name: str):
    print(f"\n=======================================================")
    print(f"Testing URL: {url} ({name})")
    print(f"=======================================================")
    
    console_logs = []
    page_errors = []
    failed_requests = []
    responses = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        page.on("console", lambda msg: console_logs.append(f"[{msg.type.upper()}] {msg.text} (location: {msg.location})"))
        page.on("pageerror", lambda err: page_errors.append(f"{type(err).__name__}: {str(err)}"))
        page.on("requestfailed", lambda req: failed_requests.append(f"{req.method} {req.url} -> {req.failure}"))
        page.on("response", lambda resp: responses.append({
            "url": resp.url,
            "status": resp.status,
            "content_type": resp.headers.get("content-type", "")
        }))
        
        try:
            resp = page.goto(url, wait_until="networkidle", timeout=15000)
            page_status = resp.status if resp else "No response"
        except Exception as e:
            print(f"Navigation exception: {e}")
            page_status = "Navigation timed out or errored"
        
        # Wait extra time for React lifecycle
        page.wait_for_timeout(2000)
        
        # Capture DOM inside #root
        root_info = page.evaluate("""() => {
            const root = document.getElementById('root');
            if (!root) return { exists: false };
            return {
                exists: true,
                childElementCount: root.childElementCount,
                innerHTML: root.innerHTML,
                innerText: root.innerText,
                offsetWidth: root.offsetWidth,
                offsetHeight: root.offsetHeight,
                computedDisplay: window.getComputedStyle(root).display,
                computedVisibility: window.getComputedStyle(root).visibility,
                computedOpacity: window.getComputedStyle(root).opacity,
            };
        }""")
        
        screenshot_path = REPORTS_DIR / f"screenshot_{name}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"Screenshot saved to: {screenshot_path}")
        
        print(f"HTTP Status: {page_status}")
        print(f"Root info: {json.dumps(root_info, indent=2)}")
        print(f"\nPage Errors ({len(page_errors)}):")
        for err in page_errors:
            print(f"  - {err}")
            
        print(f"\nConsole Logs ({len(console_logs)}):")
        for log in console_logs:
            print(f"  - {log}")
            
        print(f"\nFailed Requests ({len(failed_requests)}):")
        for req in failed_requests:
            print(f"  - {req}")
            
        print(f"\nScript & Key Asset Responses:")
        for r in responses:
            if "js" in r["url"] or "css" in r["url"] or "api" in r["url"] or r["url"].endswith("/"):
                print(f"  - [{r['status']}] {r['url']} ({r['content_type']})")
                
        browser.close()
        
    return {
        "url": url,
        "root_info": root_info,
        "page_errors": page_errors,
        "console_logs": console_logs,
        "failed_requests": failed_requests
    }

if __name__ == "__main__":
    res_8000 = test_url("http://127.0.0.1:8000/", "port_8000_reproduce")
    res_5173 = test_url("http://127.0.0.1:5173/", "port_5173_reproduce")
