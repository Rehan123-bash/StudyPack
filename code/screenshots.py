"""Take screenshots of real runs in the StudyPack app (used for the Milestone 2 report).

Start the app first (with GEMINI_API_KEY set), then run:
    streamlit run code/app.py --server.headless true &
    python code/screenshots.py
Screenshots are saved to docs/screenshots/.
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"

# (test number, sample name, tab to open, file name)
SHOTS = [
    (1, "T01_os_deadlocks", "Practice questions", "test01_questions.png"),
    (8, "T08_thin_compiler", "Gaps in your notes", "test08_gaps.png"),
    (11, "T11_injection_dns", "Practice questions", "test11_injection.png"),
]


def run(page, sample, tab, fname):
    page.goto(URL)
    page.get_by_text("Or try a sample from our test set").wait_for(timeout=60000)
    page.get_by_test_id("stSelectbox").filter(has_text="Or try a sample").click()
    page.get_by_role("option", name=sample, exact=True).click()
    page.wait_for_timeout(1500)
    page.get_by_role("button", name="Build study pack").click()
    page.get_by_text("Study pack:").wait_for(timeout=300000)  # 4 API calls on the free tier
    page.wait_for_timeout(1500)
    page.get_by_role("tab", name=tab).click()
    page.wait_for_timeout(800)
    if tab == "Practice questions":
        page.get_by_text("Show answer").first.click()
        page.wait_for_timeout(800)
    page.get_by_text("Study pack:").scroll_into_view_if_needed()
    page.screenshot(path=str(OUT / fname), full_page=True)
    print("saved", fname)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get("CHROME_PATH") or None)
        page = browser.new_page(viewport={"width": 1300, "height": 2400})
        for no, sample, tab, fname in SHOTS:
            try:
                run(page, sample, tab, fname)
            except Exception as e:
                print(f"test {no} failed: {e}")
                page.screenshot(path=str(OUT / f"error_{fname}"), full_page=True)
        browser.close()


if __name__ == "__main__":
    main()
