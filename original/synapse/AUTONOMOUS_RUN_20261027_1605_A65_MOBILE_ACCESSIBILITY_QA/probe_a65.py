"""A65: isolated headless-browser audit, never touches user browser/profile."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
D=Path(__file__).resolve().parent
A64=D.parent/"AUTONOMOUS_RUN_20261027_1550_A64_INTEGRATION_RECONCILIATION"/"OUTPUT"/"comparison.html"
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
def main():
    results={}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=CHROME,headless=True,args=["--disable-gpu","--no-first-run","--disable-extensions"])
        try:
            for name,width,height in [("desktop",1440,900),("mobile",390,844)]:
                page=browser.new_page(viewport={"width":width,"height":height},device_scale_factor=1)
                page.goto(A64.as_uri(),wait_until="load")
                stats=page.evaluate("""() => ({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
                    tableCount:document.querySelectorAll('table').length,
                    rowCount:document.querySelectorAll('tbody tr').length,
                    sourceBanner:document.body.innerText.includes('DERIVED SIMULATION'),
                    heading:document.querySelector('h1')?.textContent})""")
                results[name]=stats
                page.screenshot(path=str(D/(name+"_original.png")),full_page=True)
                page.close()
        finally:browser.close()
    (D/"ORIGINAL_A64_BROWSER_PROBE.json").write_text(json.dumps(results,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(results))
if __name__=="__main__":main()
