from __future__ import annotations

import unittest
from datetime import date

from bot.checker import qualifying_dates
from bot.dates import calendar_grid_dates


class QualifyingDatesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.deadline = date(2026, 8, 7)
        self.today = date(2026, 6, 23)

    def test_august_6_qualifies_before_deadline(self) -> None:
        self.assertEqual(
            qualifying_dates([date(2026, 8, 6)], self.deadline, self.today),
            [date(2026, 8, 6)],
        )

    def test_false_july_6_would_have_qualifed_under_old_logic(self) -> None:
        self.assertEqual(
            qualifying_dates([date(2026, 7, 6)], self.deadline, self.today),
            [date(2026, 7, 6)],
        )

    def test_july_calendar_link_index_maps_to_august_not_july(self) -> None:
        grid = calendar_grid_dates(2026, 7)
        available_index = 38  # bottom-row "6" in juli 2026 view
        slot_date = grid[available_index]
        self.assertEqual(slot_date, date(2026, 8, 6))
        self.assertNotEqual(slot_date, date(2026, 7, 6))

    def test_deadline_and_past_dates_are_excluded(self) -> None:
        self.assertEqual(
            qualifying_dates(
                [date(2026, 8, 7), date(2026, 8, 6), date(2026, 6, 1)],
                self.deadline,
                self.today,
            ),
            [date(2026, 8, 6)],
        )


if __name__ == "__main__":
    unittest.main()
