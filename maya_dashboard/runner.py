"""Selenium runner; opens one article item but never downloads or submits."""

from pathlib import Path
from time import perf_counter, sleep
from urllib.parse import urlsplit

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .checks import inspect_schedule, safe_excerpt
from .service import MAYA_ORIGIN

MAYA_HOSTS = {"binusmaya.binus.ac.id", "lms.binus.ac.id"}


def open_browser(config):
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={config.data_dir / 'chrome-profile'}")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-notifications")
    config.data_dir.mkdir(parents=True, exist_ok=True)
    return webdriver.Chrome(options=options)


def _has(driver, selector):
    return bool(driver.find_elements(By.CSS_SELECTOR, selector))


def open_schedule_via_lms(driver, emit):
    """Enter LMS through Maya's launcher; deep links alone redirect home."""
    driver.get(MAYA_ORIGIN + "/")
    try:
        launcher = WebDriverWait(driver, 8).until(
            lambda d: next((tile for image in d.find_elements(By.CSS_SELECTOR, 'img[alt="LMS"]')
                            if image.is_displayed()
                            for tile in [image.find_element(By.XPATH, "..")]
                            if tile.is_displayed()), None)
        )
    except TimeoutException:
        emit("authentication", "failed", "Saved Maya session is unavailable; log in to the dedicated Chrome profile before retrying.")
        return False
    original = driver.current_window_handle
    before = set(driver.window_handles)
    emit("navigation", "running", "Clicking LMS launcher.")
    launcher.click()
    try:
        new_handle = WebDriverWait(driver, 15).until(
            lambda d: next(iter(set(d.window_handles) - before), None)
        )
        driver.switch_to.window(new_handle)
    except Exception:
        driver.switch_to.window(original)  # Some Maya versions may open in the same tab.
    menu = WebDriverWait(driver, 25).until(
        lambda d: next((el for el in d.find_elements(By.XPATH, "//*[normalize-space(text())='Schedule']")
                        if el.is_displayed()), None)
    )
    emit("navigation", "running", "Clicking Schedule menu.")
    menu.click()
    WebDriverWait(driver, 25).until(lambda d: _has(d, ".p-schedule h3.page-title-global"))
    emit("navigation", "passed", "Opened My Schedule through LMS.")
    return True


def open_materials_from_schedule(driver, config, section="LA83 - LEC", session="Session 2"):
    """Open a visible class card, preferring the configured session when present."""
    cards = driver.find_elements(By.CSS_SELECTOR, ".p-schedule .schedule-data .c-schedule-container")
    candidates = []
    for card in cards:
        def texts(css):
            return [element.text.strip() for element in card.find_elements(By.CSS_SELECTOR, css)]
        titles, sections = texts(".schedule-desc"), texts(".schedule-title")
        if card.is_displayed() and any(titles) and any(sections):
            preferred = (config.course_title in titles and section in sections and
                         session in texts(".feature-label"))
            candidates.append((not preferred, card, titles[0]))
    if not candidates:
        raise AssertionError("No populated class card was found in this month's schedule")
    preferred_missing, card, course_title = sorted(candidates, key=lambda item: item[0])[0]
    before = set(driver.window_handles)
    card.click()
    new_handles = set(driver.window_handles) - before
    if new_handles:
        driver.switch_to.window(next(iter(new_handles)))
    WebDriverWait(driver, 25).until(lambda d: any(el.text.strip() for el in
                                     d.find_elements(By.CSS_SELECTOR, ".header-main-couse-detail h1")))
    opened = urlsplit(driver.current_url)
    if opened.scheme != "https" or opened.hostname not in MAYA_HOSTS:
        raise AssertionError("Schedule card did not open a Maya course session")
    return course_title


def first_material_after_video_conference(driver):
    """Return the article's main clickable area, never Download or Report."""
    rows = driver.find_elements(By.CSS_SELECTOR, "#thingstodocontainer .activity-item-lms")
    for index, row in enumerate(rows):
        labels = row.find_elements(By.CSS_SELECTOR, ".resource-item .break-word span")
        if any(label.text.strip() == "Video Conference" for label in labels):
            if index + 1 < len(rows):
                targets = rows[index + 1].find_elements(By.CSS_SELECTOR, "div[id^='id_offline_'].pointer")
                return next((target for target in targets if target.is_displayed()), None)
            return None
    return None


def _capture(driver, evidence_dir, name):
    # Never capture an authentication page (could show MFA or credentials).
    location = urlsplit(driver.current_url)
    course_view = (name == "materials" and location.scheme == "https" and
                   location.hostname in MAYA_HOSTS and
                   location.path.startswith("/lms/course/") and "/session/" in location.path)
    article_view = (name == "materials" and location.scheme == "https" and
                    location.hostname == "lms.binus.ac.id" and
                    bool(location.path.removeprefix("/lms/view-article/")) and
                    location.path.startswith("/lms/view-article/"))
    if (_has(driver, "input[type='password']") or
            not (_has(driver, ".p-schedule h3.page-title-global") or
                 _has(driver, ".header-main-couse-detail h1") or course_view or article_view)):
        return None, "Authentication or unknown page: evidence capture skipped"
    filename = f"{name}.png"
    try:
        saved = driver.save_screenshot(str(evidence_dir / filename))
        screenshot = filename if saved else None
    except Exception:
        screenshot = None
    try:
        excerpt = safe_excerpt(driver.find_element(By.TAG_NAME, "body").text)
    except Exception:
        excerpt = "Page text unavailable"
    return screenshot, excerpt


def run_maya(config, emit, evidence_dir, browser_factory=None, sleep_fn=sleep):
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    browser = (browser_factory or open_browser)(config)
    try:
        if not open_schedule_via_lms(browser, emit):
            return
        for name in ("schedule", "materials"):
            emit(name, "running", "Opening page and checking visible content.")
            started = perf_counter()
            count = None
            error = None
            waited = False
            try:
                if name == "materials":
                    open_materials_from_schedule(browser, config, config.section, config.session)
                    WebDriverWait(browser, 20).until(lambda d: _has(d, ".header-main-couse-detail h1"))
                    try:
                        target = WebDriverWait(browser, 5).until(first_material_after_video_conference)
                    except TimeoutException:
                        raise AssertionError("No clickable material immediately below Video Conference was found") from None
                    emit(name, "running", "Opening the first material below Video Conference.")
                    before = set(browser.window_handles)
                    target.click()
                    new_handles = set(browser.window_handles) - before
                    if new_handles:
                        browser.switch_to.window(next(iter(new_handles)))
                    emit(name, "running", "Waiting 10 seconds for the opened material before screenshot.")
                    sleep_fn(10)
                    waited = True
                    count = 1
                else:
                    WebDriverWait(browser, 25).until(lambda d: any(
                        el.text.strip() for el in d.find_elements(
                            By.CSS_SELECTOR, ".p-schedule .schedule-data .c-schedule-container .schedule-desc")))
                    emit(name, "running", "Waiting 2 seconds for page content before capturing evidence.")
                    sleep_fn(2)
                    waited = True
                    count = inspect_schedule(browser)
            except AssertionError as exc:
                error = str(exc)  # Only our fixed assertion messages, never page data.
            except Exception:
                error = "Page did not load or its expected elements changed."
            if not waited:
                emit(name, "running", "Waiting 2 seconds before capturing evidence, if the page is available.")
                sleep_fn(2)
            screenshot, excerpt = _capture(browser, evidence_dir, name)
            if name == "materials" and not error and not screenshot:
                error = "Material was opened, but a safe screenshot could not be captured."
            duration_ms = int((perf_counter() - started) * 1000)
            if error:
                emit(name, "failed", error, screenshot=screenshot, excerpt=excerpt, duration_ms=duration_ms)
            else:
                detail = (f"Found {count} class cards." if name == "schedule" else
                          "Opened the first material below Video Conference and captured evidence.")
                emit(name, "passed", detail, count,
                     screenshot=screenshot, excerpt=excerpt, duration_ms=duration_ms)
    finally:
        browser.quit()
