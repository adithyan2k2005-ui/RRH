from playwright.sync_api import sync_playwright

def verify():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        for port in [5173, 8000]:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.goto(f"http://127.0.0.1:{port}/", wait_until="networkidle")
            page.wait_for_timeout(1000)
            
            content = page.content()
            has_design_insp = "Official Design Inspiration" in content
            has_brand_desc = "iconic royal burgundy" in content
            has_hackathon_tag = "Independent Hackathon Analytics System" in content
            
            img_count = page.locator("img[alt*='Rajasthan Royals']").count()
            emblem_visible = page.locator("img[alt='Rajasthan Royals emblem']").is_visible()
            
            page.screenshot(path=f"reports/master_verification/screenshots/overview_after_content_removal_{port}.png")
            print(f"Port {port}:")
            print(f"  has_design_inspiration: {has_design_insp}")
            print(f"  has_brand_desc:          {has_brand_desc}")
            print(f"  has_hackathon_tag:       {has_hackathon_tag}")
            print(f"  emblem_images_found:     {img_count}")
            print(f"  emblem_card_visible:     {emblem_visible}")
        browser.close()

if __name__ == "__main__":
    verify()
