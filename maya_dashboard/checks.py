"""Read-only assertions against the Maya DOM. Never click resource actions."""

from selenium.webdriver.common.by import By


def inspect_schedule(driver):
    heading = driver.find_elements(By.CSS_SELECTOR, ".p-schedule h3.page-title-global")
    if not heading or heading[0].text.strip() != "My Schedule":
        raise AssertionError("Schedule heading was not found")
    if not driver.find_elements(By.CSS_SELECTOR, ".p-schedule .schedule-calendar .bm7__MonthDates"):
        raise AssertionError("Schedule calendar was not found")
    cards = [card for card in driver.find_elements(By.CSS_SELECTOR, ".p-schedule .schedule-data .c-schedule-container")
             if any(el.text.strip() for el in card.find_elements(By.CSS_SELECTOR, ".schedule-title"))
             and any(el.text.strip() for el in card.find_elements(By.CSS_SELECTOR, ".schedule-desc"))]
    if not cards:
        raise AssertionError("No class card was found in the schedule")
    return len(cards)


def inspect_materials(driver, expected_course=None):
    headings = driver.find_elements(By.CSS_SELECTOR, ".header-main-couse-detail h1")
    if not headings or not headings[0].text.strip():
        raise AssertionError("Course heading was not found")
    if expected_course and headings[0].text.strip() != expected_course:
        raise AssertionError("Configured course title did not match")
    if not driver.find_elements(By.CSS_SELECTOR, "#tabClassDetailWrapper #session .nav-link.active"):
        raise AssertionError("Course session tab was not active")
    items = driver.find_elements(By.CSS_SELECTOR, "#thingstodocontainer .activity-item-lms .resource-item")
    if not items:
        raise AssertionError("No learning-material item was found in this session")
    return len(items)


def safe_excerpt(page_text):
    """Only emit allowlisted UI labels; raw Maya text may hold tokens and PII."""
    labels = ("My Schedule", "Things to do in this session", "Session", "Learning Outcome")
    return " | ".join(label for label in labels if label in page_text) or "No allowlisted UI labels found"
