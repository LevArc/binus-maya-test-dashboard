import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from maya_dashboard.checks import inspect_schedule, inspect_materials, safe_excerpt


class CheckTests(unittest.TestCase):
    def test_schedule_requires_calendar_and_class_cards(self):
        driver = Mock()
        card = Mock()
        card.find_elements.side_effect = lambda by, css: [SimpleNamespace(text="LA83 - LEC" if css == ".schedule-title" else "Automation Testing")]
        driver.find_elements.side_effect = lambda by, css: {
            ".p-schedule h3.page-title-global": [SimpleNamespace(text="My Schedule")],
            ".p-schedule .schedule-calendar .bm7__MonthDates": [object()],
            ".p-schedule .schedule-data .c-schedule-container": [card, card],
        }.get(css, [])
        self.assertEqual(inspect_schedule(driver), 2)

    def test_schedule_rejects_empty_class_list(self):
        driver = Mock()
        driver.find_elements.side_effect = lambda by, css: {
            ".p-schedule h3.page-title-global": [SimpleNamespace(text="My Schedule")],
            ".p-schedule .schedule-calendar .bm7__MonthDates": [object()],
        }.get(css, [])
        with self.assertRaisesRegex(AssertionError, "class card"):
            inspect_schedule(driver)

    def test_schedule_rejects_loading_placeholder_cards(self):
        driver = Mock()
        placeholder = Mock()
        placeholder.find_elements.return_value = []
        driver.find_elements.side_effect = lambda by, css: {
            ".p-schedule h3.page-title-global": [SimpleNamespace(text="My Schedule")],
            ".p-schedule .schedule-calendar .bm7__MonthDates": [object()],
            ".p-schedule .schedule-data .c-schedule-container": [placeholder, placeholder, placeholder],
        }.get(css, [])
        with self.assertRaisesRegex(AssertionError, "class card"):
            inspect_schedule(driver)

    def test_materials_require_course_header_session_and_item(self):
        driver = Mock()
        driver.find_elements.side_effect = lambda by, css: {
            ".header-main-couse-detail h1": [SimpleNamespace(text="Automation Testing")],
            "#tabClassDetailWrapper #session .nav-link.active": [object()],
            "#thingstodocontainer .activity-item-lms .resource-item": [object()],
        }.get(css, [])
        self.assertEqual(inspect_materials(driver), 1)

    def test_materials_reject_wrong_course(self):
        driver = Mock()
        driver.find_elements.side_effect = lambda by, css: {
            ".header-main-couse-detail h1": [SimpleNamespace(text="Other Course")],
            "#tabClassDetailWrapper #session .nav-link.active": [object()],
            "#thingstodocontainer .activity-item-lms .resource-item": [object()],
        }.get(css, [])
        with self.assertRaisesRegex(AssertionError, "course title"):
            inspect_materials(driver, expected_course="Automation Testing")

    def test_excerpt_redacts_secrets_and_personal_content(self):
        text = "Student Edward JWT eyJhbGciOiJub25lIn0.eyJzdWIiOiJ4In0.signature token=abcd1234"
        excerpt = safe_excerpt(text)
        self.assertNotIn("Edward", excerpt)
        self.assertNotIn("eyJhb", excerpt)
        self.assertNotIn("abcd1234", excerpt)


if __name__ == "__main__":
    unittest.main()
