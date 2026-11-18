from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    for port in [8000, 5173]:
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        url = f"http://127.0.0.1:{port}/"
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(1000)
        
        info = page.evaluate("""() => {
            const root = document.getElementById('root');
            const fullText = root ? root.innerText : '';
            const hasRREmblemText = /RR\\s+Emblem/i.test(fullText);
            const img = document.querySelector("img[alt*='Rajasthan Royals']");
            return {
                hasRREmblemText,
                imgFound: !!img,
                imgSrc: img ? img.src.slice(-35) : null,
                imgAlt: img ? img.alt : null,
                textSnippet: fullText.slice(0, 300).replace(/\\n+/g, ' ')
            };
        }""")
        
        page.screenshot(path=f"reports/phase7/screenshot_emblem_fixed_{port}.png")
        print(f"Port {port}:")
        print(f"  hasRREmblemText: {info['hasRREmblemText']}")
        print(f"  imgFound: {info['imgFound']}")
        print(f"  imgAlt: {info['imgAlt']}")
        print(f"  imgSrc: {info['imgSrc']}")
        print(f"  textSnippet: {info['textSnippet'][:120]}")
    browser.close()
