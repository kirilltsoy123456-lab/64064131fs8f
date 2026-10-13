import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from attendance_bot.time_format import format_local_time


class FormatLocalTimeTests(unittest.TestCase):
    def test_formats_astana_time_with_offset(self) -> None:
        local_time = datetime(2026, 10, 13, 9, 30, tzinfo=ZoneInfo("Asia/Almaty"))
        self.assertEqual(
            format_local_time(local_time),
            "13.10.2026 09:30:00 (Астана, UTC+05:00)",
        )


if __name__ == "__main__":
    unittest.main()
