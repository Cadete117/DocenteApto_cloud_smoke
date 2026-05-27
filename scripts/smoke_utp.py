from pathlib import Path
import os

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync


URL = os.getenv("UTP_URL", "https://class.utp.edu.pe")
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "artifacts-smoke"))


def main():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel=os.getenv("PLAYWRIGHT_CHANNEL", "chrome"),
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-default-browser-check",
                "--no-first-run",
                "--no-sandbox",
            ],
        )

        context = browser.new_context(
            locale="es-PE",
            timezone_id="America/Lima",
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            ),
            extra_http_headers={
                "Accept-Language": "es-PE,es;q=0.9,en-US;q=0.8,en;q=0.7",
            },
        )

        trace_path = ARTIFACTS_DIR / "trace.zip"
        context.tracing.start(screenshots=True, snapshots=True, sources=True)

        page = context.new_page()
        stealth_sync(page)
        page.on("console", lambda msg: print(f"[browser:{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: print(f"[pageerror] {exc}"))
        page.on(
            "response",
            lambda response: print(f"[http:{response.status}] {response.url}")
            if response.status >= 400
            else None,
        )

        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(15000)
            page.screenshot(path=str(ARTIFACTS_DIR / "inicio.png"), full_page=True)
            (ARTIFACTS_DIR / "inicio.html").write_text(page.content(), encoding="utf-8")

            text = page.locator("body").inner_text(timeout=5000).strip()
            print(f"Titulo: {page.title()!r}")
            print(f"Texto visible: {text[:1000]!r}")

            if not text and page.locator("input").count() == 0:
                raise RuntimeError("La pagina cargo sin texto visible ni inputs.")
        finally:
            context.tracing.stop(path=str(trace_path))
            browser.close()


if __name__ == "__main__":
    main()
