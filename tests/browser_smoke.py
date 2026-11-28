"""Exercise the published records explorer at a project subpath in Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "dist", Path(temporary) / "pantryprices")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=temporary))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_BIN"))
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/pantryprices/")
                page.wait_for_function("document.querySelector('#edition').textContent.includes('UTC')")
                page.wait_for_selector("#ingredients input")
                page.select_option("#first", "2017-09")
                assert "$9.69" in page.locator("#facts").inner_text()
                page.select_option("#second", "2026-09")
                assert "$13.99" in page.locator("#facts").inner_text()
                assert "Nova Scotia" in page.locator("#regional").inner_text()
                page.select_option("#region", "Nova Scotia")
                assert "$14.68" in page.locator("#facts").inner_text()
                page.select_option("#region", "Yellowknife, Northwest Territories")
                assert "Unreported" in page.locator("#facts").inner_text()
                page.select_option("#frequency", "annual")
                page.select_option("#region", "Canada")
                assert page.locator('#second option[value="2025"]').count() == 1
                page.select_option("#series", "print")
                assert "133.0¢" in page.locator("#facts").inner_text()
                page.select_option("#series", "survey")
                assert page.locator("#first option").first.get_attribute("value") == "1995-01"
                page.select_option("#series", "yearbook")
                assert "$3.15" in page.locator("#facts").inner_text()
                assert "$55.04" in page.locator("#facts").inner_text()
                page.select_option("#second", "1985")
                assert "Unreported" in page.locator("#facts").inner_text()
                page.select_option("#series", "urban")
                assert "53.6¢" in page.locator("#facts").inner_text()
                page.get_by_label("Eggs (dozen)").fill("0.25")
                assert "0.25 × dozen" in page.locator("#breakdown").inner_text()
                page.get_by_label("Eggs (dozen)").fill("-1")
                assert page.locator("#csv").is_disabled()
                page.locator("#reset").click()
                page.locator('#trend button[aria-label^="1920"]').click()
                assert page.locator("#second").input_value()=="1920"
                assert "114.6¢" in page.locator("#facts").inner_text()
                assert page.locator("#breakdown a").count()==2
                with page.expect_download() as capture:
                    page.locator("#csv").click()
                download = capture.value
                assert download.suggested_filename.endswith(".csv")
                assert len(Path(download.path()).read_text().splitlines()) >= 2
                page.select_option("#series","scanner")
                page.select_option("#coffee-start", "2024-01")
                page.select_option("#coffee-end", "2025-01")
                page.select_option("#coffee-threshold", "-10")
                assert page.locator("#coffee-rows tr").count() == 13
                assert page.locator("#coffee-events li").count() == 3
                assert "2024-01 to 2025-01" in page.locator("#coffee-result").inner_text()
                assert page.locator("#coffee-chart path").count() == 3
                assert page.locator("#coffee-first option").count() == 10
                page.select_option("#coffee-first", "on")
                page.select_option("#coffee-second", "ab")
                assert "Ontario" in page.locator("#coffee-legend").inner_text()
                assert "Alberta" in page.locator("#coffee-events").inner_text()
                assert page.locator("#coffee-start").input_value() == "2024-01"
                assert "Ontario" in page.locator("#coffee-first-price").text_content()
                assert "Alberta" in page.locator("#coffee-second-price").text_content()
                assert page.locator(".coffee-provinces tbody tr").count() == 10
                page.locator(".coffee-provinces summary").click()
                page.locator(".coffee-provinces").get_by_role("link", name="Quebec").click()
                page.wait_for_function("document.querySelector('#coffee-first').value === 'qc'")
                assert "Quebec" in page.locator("#coffee-result").text_content()
                with page.expect_download() as coffee_capture:
                    page.get_by_role("link", name="Download all monthly coffee prices").click()
                assert "arabica_cad_per_kg" in Path(coffee_capture.value.path()).read_text()
                page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                assert not errors, errors
                browser.close()
            print("Browser checks passed: source records, filters, CSV download and mobile layout")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
