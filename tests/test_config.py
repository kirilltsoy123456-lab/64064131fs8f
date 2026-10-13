import unittest
from datetime import time

from attendance_bot.config import parse_reminder_times


class ParseReminderTimesTests(unittest.TestCase):
    def test_parses_multiple_times(self) -> None:
        self.assertEqual(
            parse_reminder_times("09:00, 18:30"),
            [time(9, 0), time(18, 30)],
        )

    def test_rejects_invalid_time(self) -> None:
        with self.assertRaises(ValueError):
            parse_reminder_times("25:00")

    def test_rejects_empty_schedule(self) -> None:
        with self.assertRaises(ValueError):
            parse_reminder_times(" , ")


if __name__ == "__main__":
    unittest.main()
