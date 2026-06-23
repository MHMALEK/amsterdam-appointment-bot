from __future__ import annotations

import unittest
from datetime import date

from bot.dates import calendar_grid_dates, month_label_for_date, slot_datetime_from_date


class CalendarGridDatesTests(unittest.TestCase):
    def test_july_2026_grid_starts_with_june_overflow(self) -> None:
        grid = calendar_grid_dates(2026, 7)
        self.assertEqual(grid[0], date(2026, 6, 29))
        self.assertEqual(grid[2], date(2026, 7, 1))

    def test_july_2026_day_6_in_second_row_is_july(self) -> None:
        grid = calendar_grid_dates(2026, 7)
        self.assertEqual(grid[7], date(2026, 7, 6))

    def test_july_2026_overflow_day_6_in_bottom_row_is_august(self) -> None:
        grid = calendar_grid_dates(2026, 7)
        self.assertEqual(grid[38], date(2026, 8, 6))

    def test_august_2026_view_contains_august_6(self) -> None:
        grid = calendar_grid_dates(2026, 8)
        self.assertIn(date(2026, 8, 6), grid)
        self.assertEqual(grid[grid.index(date(2026, 8, 6))], date(2026, 8, 6))

    def test_month_label_for_date(self) -> None:
        self.assertEqual(month_label_for_date(date(2026, 8, 6)), "augustus 2026")

    def test_slot_datetime_from_date(self) -> None:
        when = slot_datetime_from_date(date(2026, 8, 6), "14:00")
        self.assertEqual(when.year, 2026)
        self.assertEqual(when.month, 8)
        self.assertEqual(when.day, 6)
        self.assertEqual(when.hour, 14)
        self.assertEqual(when.minute, 0)


if __name__ == "__main__":
    unittest.main()
