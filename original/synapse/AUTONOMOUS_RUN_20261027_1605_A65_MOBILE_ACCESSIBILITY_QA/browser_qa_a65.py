"""A65 browser regression and independent content-preservation checks."""
import hashlib,json
from pathlib import Path
from playwright.sync_api import sync_playwright
import a65_mobile_reflow as m
D=Path(__file__).resolve().parent
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    src=m.SRC.read_text(encoding="utf-8")
    mobile=m.OUT.read_text(encoding="utf-8")
    assert mobile.count('data-label=')==60
    assert mobile.count('DERIVED SIMULATION')==src.count('DERIVED SIMULATION')==1
    assert mobile.count('<tr>')==src.count('<tr>')==12
    assert mobile.count('<td')==src.count('<td')==60
    assert mobile.count('20.000398')==src.count('20.000398')
    browser_data={}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=CHROME,headless=True,args=["--disable-gpu","--disable-extensions","--no-first-run"])
        try:
            for label,w,h in (("mobile_390",390,844),("mobile_320",320,640),("desktop_1440",1440,900)):
                page=browser.new_page(viewport={"width":w,"height":h},device_scale_factor=1)
                page.goto(m.OUT.as_uri(),wait_until="load")
                result=page.evaluate("""() => ({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
                  tables:document.querySelectorAll('table').length,rows:document.querySelectorAll('tbody tr').length,
                  cells:document.querySelectorAll('tbody td[data-label]').length,
                  banner:document.body.innerText.includes('DERIVED SIMULATION'),
                  mobileLabel:getComputedStyle(document.querySelector('tbody td'),'::before').content})""")
                assert result["scrollWidth"]<=result["width"],(label,result)
                assert result["tables"]==2 and result["rows"]==10 and result["cells"]==60 and result["banner"]
                if w<=700:assert "Kanál" in result["mobileLabel"]
                browser_data[label]=result
                page.screenshot(path=str(D/(label+".png")),full_page=True)
                page.close()
        finally:browser.close()
    report={"qa":"PASS","screens":browser_data,"original_sha256":sha(m.SRC),
            "mobile_sha256":sha(m.OUT),"physical_release":False,"source_kind":"derived_simulation"}
    (D/"BROWSER_QA_A65.json").write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=True))
if __name__=="__main__":main()
