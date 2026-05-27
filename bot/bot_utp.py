from datetime import datetime
from pathlib import Path
import os

from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

load_dotenv()

USER = os.getenv("UTP_USER")
PASS = os.getenv("UTP_PASS")
UTP_URL = os.getenv("UTP_URL", "https://class.utp.edu.pe")
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "artifacts"))


def _env_bool(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "si"}


def _save_debug(page, label):
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_label = label.replace(" ", "_").lower()
    screenshot_path = ARTIFACTS_DIR / f"{safe_label}.png"
    html_path = ARTIFACTS_DIR / f"{safe_label}.html"

    try:
        page.screenshot(path=str(screenshot_path), full_page=True)
    except Exception as exc:
        print(f"No se pudo guardar screenshot {screenshot_path}: {exc}")

    try:
        html_path.write_text(page.content(), encoding="utf-8")
    except Exception as exc:
        print(f"No se pudo guardar HTML {html_path}: {exc}")

    print(f"Diagnostico guardado: {screenshot_path} / {html_path}")


def _new_context(browser):
    context = browser.new_context(
        accept_downloads=True,
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

    context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['es-PE', 'es', 'en-US', 'en'] });
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        window.chrome = window.chrome || { runtime: {} };
        """
    )

    return context


def _wait_for_login(page):
    try:
        page.wait_for_selector('input[type="text"]', timeout=120000)
    except PlaywrightTimeoutError:
        _save_debug(page, "login_no_cargo")
        title = page.title()
        body_text = page.locator("body").inner_text(timeout=5000) if page.locator("body").count() else ""
        raise RuntimeError(
            "No cargo el formulario de login de UTP+CLASS. "
            f"Titulo: {title!r}. Texto visible: {body_text[:500]!r}"
        )


def subir_csv_inscripciones(csv_path):
    if not USER or not PASS:
        raise RuntimeError("Faltan las variables UTP_USER y/o UTP_PASS.")

    nombre_archivo = os.path.basename(csv_path)
    headless = _env_bool("PLAYWRIGHT_HEADLESS", False)
    slow_mo = int(os.getenv("PLAYWRIGHT_SLOW_MO", "0"))
    channel = os.getenv("PLAYWRIGHT_CHANNEL", "chrome").strip() or None

    launch_options = {
        "headless": headless,
        "slow_mo": slow_mo,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-default-browser-check",
            "--no-first-run",
            "--no-sandbox",
            "--start-maximized",
        ],
    }

    if channel:
        launch_options["channel"] = channel

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_options)
        context = _new_context(browser)
        trace_path = ARTIFACTS_DIR / "trace.zip"
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
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
            print("Iniciando sesion...")
            page.goto(UTP_URL, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(12000)
            _save_debug(page, "01_inicio")

            _wait_for_login(page)

            input_user = page.locator('input[type="text"]').first
            input_pass = page.locator('input[type="password"]').first

            input_user.fill(USER)
            input_pass.fill(PASS)

            page.locator("button:has-text('Iniciar sesi')").first.click()

            page.wait_for_timeout(10000)
            _save_debug(page, "02_post_login")

            print("Seleccionando Administrador...")
            rol_admin = page.locator("div.text-center:has(p:has-text('Administrador'))").first
            rol_admin.wait_for(state="visible", timeout=90000)
            rol_admin.click()

            page.get_by_role("button", name="Continuar").click()
            page.wait_for_timeout(10000)
            _save_debug(page, "03_administrador")

            print("Subiendo CSV...")
            page.set_input_files('input[type="file"]', csv_path)
            page.wait_for_timeout(5000)

            print("Procesando archivo...")
            boton_procesar = page.locator(
                "button[data-testid='cc-button__element']:has-text('Procesar')"
            ).first
            boton_procesar.wait_for(state="visible", timeout=60000)
            boton_procesar.click()

            print("Esperando procesamiento...")
            page.wait_for_timeout(120000)

            print("Recargando pagina...")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(10000)
            _save_debug(page, "04_reporte")

            print("Buscando reporte...")
            filas = page.locator("div[data-testid='file-list-buttons-container']").locator(
                "xpath=../../.."
            )

            total = filas.count()
            if total == 0:
                raise RuntimeError("No se encontraron reportes.")

            for i in range(total):
                fila = filas.nth(i)
                if fila.locator(f"text={nombre_archivo}").count() > 0:
                    print(f"Reporte encontrado en fila {i}")
                    boton_descarga = fila.locator("button:has-text('Reporte parcial')").first
                    boton_descarga.wait_for(state="visible", timeout=30000)

                    with page.expect_download(timeout=60000) as download_info:
                        boton_descarga.click()

                    download = download_info.value
                    Path("reportes").mkdir(exist_ok=True)
                    ruta = (
                        f"reportes/reporte_"
                        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    )
                    download.save_as(ruta)
                    print("Reporte descargado:", ruta)
                    return ruta

            raise RuntimeError("No se encontro el reporte del archivo subido.")
        except Exception:
            _save_debug(page, "error")
            raise
        finally:
            try:
                context.tracing.stop(path=str(trace_path))
                print(f"Trace guardado: {trace_path}")
            finally:
                browser.close()
