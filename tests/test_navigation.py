import unittest
from types import SimpleNamespace
from unittest.mock import patch
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotInteractableException

from maya_dashboard.runner import open_schedule_via_lms, open_materials_from_schedule
from maya_dashboard.service import Config


class FakeElement:
    def __init__(self, text="", on_click=None, parent=None, visible=True):
        self.text = text
        self.on_click = on_click
        self.parent = parent
        self.visible = visible
    def click(self):
        if self.on_click:
            self.on_click()
    def is_displayed(self):
        return self.visible
    def find_element(self, by, selector):
        if selector == ".." and self.parent:
            return self.parent
        raise AssertionError("Unexpected element lookup")


class LauncherBrowser:
    def __init__(self):
        self.window_handles = ["home"]
        self.current_window_handle = "home"
        self.path = "/"
        self.origin = "https://binusmaya.binus.ac.id"
        self.visited = []
        self.switch_to = SimpleNamespace(window=self.switch)

    @property
    def current_url(self):
        return self.origin + self.path

    def get(self, url):
        self.visited.append(url)
        self.path = "/"

    def switch(self, handle):
        self.current_window_handle = handle
        self.path = "/lms/dashboard" if handle == "lms" else "/"

    def find_elements(self, by, selector):
        if selector == 'img[alt="LMS"]' and self.current_window_handle == "home":
            return [FakeElement(parent=FakeElement(on_click=lambda: self.window_handles.append("lms")))]
        if selector == "//*[normalize-space(text())='Schedule']" and self.current_window_handle == "lms":
            return [FakeElement("Schedule", on_click=lambda: setattr(self, "path", "/lms/schedule/2026-9"))]
        if selector == ".p-schedule h3.page-title-global" and self.path.startswith("/lms/schedule/"):
            return [FakeElement("My Schedule")]
        return []


class LauncherTests(unittest.TestCase):
    def test_clicks_visible_tile_instead_of_noninteractable_image(self):
        browser = LauncherBrowser()
        events = []
        original = browser.find_elements
        tile = FakeElement(on_click=lambda: browser.window_handles.append("lms"))
        hidden = FakeElement(parent=FakeElement(on_click=lambda: self.fail("Hidden tile clicked")), visible=False)
        image = FakeElement(on_click=lambda: (_ for _ in ()).throw(ElementNotInteractableException()), parent=tile)
        def find(by, selector):
            if selector == 'img[alt="LMS"]':
                return [hidden, image]
            return original(by, selector)
        browser.find_elements = find
        open_schedule_via_lms(browser, lambda *args: events.append(args))
        self.assertEqual(browser.path, "/lms/schedule/2026-9")
        self.assertIn(("navigation", "running", "Clicking LMS launcher."), events)

    def test_missing_saved_login_fails_without_waiting_for_manual_login(self):
        browser = LauncherBrowser()
        events = []
        with patch("maya_dashboard.runner.WebDriverWait") as wait:
            wait.return_value.until.side_effect = TimeoutException()
            result = open_schedule_via_lms(browser, lambda *args: events.append(args))
        self.assertFalse(result)
        self.assertEqual(events, [("authentication", "failed", "Saved Maya session is unavailable; log in to the dedicated Chrome profile before retrying.")])
        self.assertEqual(wait.call_count, 1)

    def test_clicks_lms_launcher_switches_new_tab_and_uses_schedule_menu(self):
        browser = LauncherBrowser()
        events = []
        open_schedule_via_lms(browser, lambda *args: events.append(args))
        self.assertEqual(browser.current_window_handle, "lms")
        self.assertEqual(browser.path, "/lms/schedule/2026-9")
        self.assertEqual(browser.visited, ["https://binusmaya.binus.ac.id/"])
        self.assertIn(("navigation", "passed", "Opened My Schedule through LMS."), events)
        self.assertNotIn(("authentication", "waiting", "Log in manually in the opened Chrome window; waiting to resume."), events)

    def test_opens_configured_course_from_schedule_card_not_direct_url(self):
        browser = LauncherBrowser()
        browser.current_window_handle = "lms"
        browser.path = "/lms/schedule/2026-9"
        class Card(FakeElement):
            def find_elements(self, by, selector):
                return {
                    ".schedule-desc": [FakeElement("Automation Testing")],
                    ".schedule-title": [FakeElement("LA83 - LEC")],
                    ".feature-label": [FakeElement("F2F"), FakeElement("Session 2")],
                }.get(selector, [])
        card = Card(on_click=lambda: setattr(browser, "path", Config().course_path))
        original = browser.find_elements
        def find(by, selector):
            if selector == ".p-schedule .schedule-data .c-schedule-container":
                return [card]
            if selector == ".header-main-couse-detail h1" and browser.path.startswith("/lms/course/"):
                return [FakeElement("Automation Testing")]
            return original(by, selector)
        browser.find_elements = find
        open_materials_from_schedule(browser, Config(), section="LA83 - LEC", session="Session 2")
        self.assertTrue(browser.path.startswith("/lms/course/"))
        self.assertEqual(browser.visited, [])

    def test_course_heading_is_accepted_when_maya_uses_a_different_course_route(self):
        browser = LauncherBrowser()
        browser.origin = "https://lms.binus.ac.id"
        browser.current_window_handle = "lms"
        browser.path = "/lms/schedule/2026-9"
        class Card(FakeElement):
            def find_elements(self, by, selector):
                return {
                    ".schedule-desc": [FakeElement("Automation Testing")],
                    ".schedule-title": [FakeElement("LA83 - LEC")],
                    ".feature-label": [FakeElement("Session 2")],
                }.get(selector, [])
        card = Card(on_click=lambda: setattr(browser, "path", "/lms/course/wrong/session/wrong"))
        browser.find_elements = lambda by, selector: ([card] if selector == ".p-schedule .schedule-data .c-schedule-container" else
            [FakeElement("Automation Testing")] if selector == ".header-main-couse-detail h1" else [])
        self.assertEqual(open_materials_from_schedule(browser, Config()), "Automation Testing")

    def test_opens_a_populated_schedule_card_when_configured_session_is_absent(self):
        browser = LauncherBrowser()
        browser.current_window_handle = "lms"
        browser.path = "/lms/schedule/2026-10"
        class Card(FakeElement):
            def find_elements(self, by, selector):
                return {
                    ".schedule-desc": [FakeElement("Another Course")],
                    ".schedule-title": [FakeElement("LA01 - LEC")],
                    ".feature-label": [FakeElement("Session 4")],
                }.get(selector, [])
        placeholder = Card(visible=False)
        card = Card(on_click=lambda: setattr(browser, "path", "/lms/course/other/session/four"))
        browser.find_elements = lambda by, selector: (
            [placeholder, card] if selector == ".p-schedule .schedule-data .c-schedule-container" else
            [FakeElement("Another Course")] if selector == ".header-main-couse-detail h1" and browser.path.startswith("/lms/course/") else [])
        self.assertEqual(open_materials_from_schedule(browser, Config()), "Another Course")
        self.assertEqual(browser.path, "/lms/course/other/session/four")


if __name__ == "__main__":
    unittest.main()
