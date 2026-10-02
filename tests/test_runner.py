import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from maya_dashboard.runner import run_maya
from maya_dashboard.service import Config


class FakeDriver:
    def __init__(self, empty_materials=False, new_tab_material=False):
        self.url = ""
        self.visited = []
        self.empty_materials = empty_materials
        self.new_tab_material = new_tab_material
        self.material_clicked = False
        self.timeline = []
        self.screenshots = []
        self.window_handles = ["home"]
        self.current_window_handle = "home"
        self.switch_to = SimpleNamespace(window=self.switch)

    @property
    def current_url(self):
        return self.url

    def switch(self, handle):
        self.timeline.append(("switch", handle))
        self.current_window_handle = handle
        self.url = ("https://binusmaya.binus.ac.id/lms/dashboard" if handle == "lms" else
                    "https://lms.binus.ac.id/lms/view-article/other" if handle == "material" else
                    "https://binusmaya.binus.ac.id/")

    def get(self, url):
        self.url = url
        self.visited.append(url)

    def find_elements(self, by, css):
        schedule = "/lms/schedule/" in self.url
        browser = self
        class Card:
            def is_displayed(self):
                return True
            def find_elements(self, by, selector):
                return {
                    ".schedule-desc": [SimpleNamespace(text="Automation Testing")],
                    ".schedule-title": [SimpleNamespace(text="LA83 - LEC")],
                    ".feature-label": [SimpleNamespace(text="F2F"), SimpleNamespace(text="Session 2")],
                }.get(selector, [])
            def click(self):
                browser.url = "https://binusmaya.binus.ac.id/lms/course/414c7563-6e80-4753-b443-8cd991d7ac3e/session/a731cedf-34b4-432f-9772-6adbec4d4687"
        if css == 'img[alt="LMS"]' and self.current_window_handle == "home":
            tile = SimpleNamespace(is_displayed=lambda: True, click=lambda: self.window_handles.append("lms"))
            return [SimpleNamespace(is_displayed=lambda: True, find_element=lambda by, selector: tile)]
        if css == "//*[normalize-space(text())='Schedule']" and self.current_window_handle == "lms":
            return [SimpleNamespace(is_displayed=lambda: True,
                                    click=lambda: setattr(self, "url", "https://binusmaya.binus.ac.id/lms/schedule/2026-9"))]
        if css == "#thingstodocontainer .activity-item-lms" and not schedule and not self.empty_materials:
            browser = self
            class Resource:
                def __init__(self, label):
                    self.label = label
                def find_elements(self, by, selector):
                    if selector == ".resource-item .break-word span":
                        return [SimpleNamespace(text=self.label)]
                    if selector == "div[id^='id_offline_'].pointer" and self.label != "Video Conference":
                        def open_material():
                            browser.material_clicked = True
                            if browser.new_tab_material:
                                browser.window_handles.append("material")
                        return [SimpleNamespace(is_displayed=lambda: True, click=open_material)]
                    return []
            return [Resource("Video Conference"), Resource("2. Software Testing Types and Techniques")]
        items = {
            ".p-schedule h3.page-title-global": [SimpleNamespace(text="My Schedule")] if schedule else [],
            ".p-schedule .schedule-calendar .bm7__MonthDates": [object()] if schedule else [],
            ".p-schedule .schedule-data .c-schedule-container": [Card(), Card()] if schedule else [],
            ".p-schedule .schedule-data .c-schedule-container .schedule-desc": [SimpleNamespace(text="Automation Testing")] if schedule else [],
            ".header-main-couse-detail h1": [SimpleNamespace(text="Automation Testing")] if not schedule and self.current_window_handle != "material" else [],
            "#tabClassDetailWrapper #session .nav-link.active": [object()] if not schedule else [],
            "#thingstodocontainer .activity-item-lms .resource-item": [object()] if not schedule and not self.empty_materials else [],
        }
        return items.get(css, [])

    def save_screenshot(self, path):
        Path(path).write_bytes(b"PNG fixture")
        self.screenshots.append(path)
        return True

    def find_element(self, by, tag):
        return SimpleNamespace(text="My Schedule Things to do in this session Student Jane token=abc")

    def quit(self):
        pass


class RunnerTests(unittest.TestCase):
    def test_material_new_maya_tab_can_be_captured_after_click(self):
        with tempfile.TemporaryDirectory() as folder:
            browser = FakeDriver(new_tab_material=True)
            events = []
            run_maya(Config(data_dir=Path(folder)), lambda *args, **kw: events.append((args, kw)),
                     Path(folder), browser_factory=lambda _: browser,
                     sleep_fn=lambda seconds: browser.timeline.append(("sleep", seconds)))
            materials = [event for event in events if event[0][:2] == ("materials", "passed")]
            self.assertEqual(len(materials), 1)
            self.assertEqual(materials[0][1]["screenshot"], "materials.png")
            self.assertLess(browser.timeline.index(("switch", "material")),
                            browser.timeline.index(("sleep", 10)))

    def test_runs_both_checks_and_captures_each_step_without_secret_excerpt(self):
        with tempfile.TemporaryDirectory() as folder:
            browser = FakeDriver()
            events = []
            sleeps = []
            run_maya(Config(data_dir=Path(folder)), lambda *args, **kw: events.append((args, kw)),
                     Path(folder), browser_factory=lambda _: browser, sleep_fn=sleeps.append)
            self.assertEqual(sleeps, [2, 10])
            self.assertFalse(any(event[0][:2] == ("authentication", "running") for event in events))
            self.assertEqual(len(browser.screenshots), 2)
            finished = [event for event in events if event[0][0] in ("schedule", "materials") and event[0][1] != "running"]
            self.assertTrue(all(isinstance(event[1].get("duration_ms"), int) for event in finished))
            self.assertEqual([event[0][1] for event in finished], ["passed", "passed"])
            self.assertTrue(browser.material_clicked)
            self.assertEqual(finished[1][1]["screenshot"], "materials.png")
            self.assertTrue(all("Jane" not in str(event) and "token=abc" not in str(event) for event in events))
            self.assertTrue(all(url.startswith("https://binusmaya.binus.ac.id/") for url in browser.visited))

    def test_material_failure_does_not_erase_schedule_success(self):
        with tempfile.TemporaryDirectory() as folder:
            browser = FakeDriver(empty_materials=True)
            events = []
            run_maya(Config(data_dir=Path(folder)), lambda *args, **kw: events.append((args, kw)),
                     Path(folder), browser_factory=lambda _: browser, sleep_fn=lambda _: None)
            self.assertEqual([(x[0][0], x[0][1]) for x in events if x[0][0] in ("schedule", "materials") and x[0][1] != "running"],
                             [("schedule", "passed"), ("materials", "failed")])
            self.assertEqual(len(browser.screenshots), 2)


if __name__ == "__main__":
    unittest.main()
