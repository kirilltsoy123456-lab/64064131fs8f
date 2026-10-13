import unittest
from datetime import datetime
from unittest.mock import Mock
from zoneinfo import ZoneInfo

from attendance_bot.sheets import ATTENDANCE_HEADERS, AttendanceSheets


class AttendanceSheetTests(unittest.TestCase):
    def test_existing_coordinate_columns_are_preserved_as_legacy(self) -> None:
        worksheet = Mock()
        worksheet.row_values.return_value = [
            "Время (локальное)",
            "Время (UTC)",
            "Telegram ID",
            "Имя",
            "Username",
            "Широта",
            "Долгота",
        ]
        worksheet.col_count = 10

        AttendanceSheets._ensure_headers(worksheet, ATTENDANCE_HEADERS)

        worksheet.update.assert_called_once()
        updated_headers = worksheet.update.call_args.kwargs["values"][0]
        self.assertIn("Широта (старые записи)", updated_headers)
        self.assertIn("Долгота (старые записи)", updated_headers)
        self.assertEqual(updated_headers[-2:], ["Тип отметки", "Местоположение"])
        self.assertEqual(updated_headers[:5], ATTENDANCE_HEADERS[:5])

    def test_new_event_saves_address_without_coordinate_columns(self) -> None:
        sheets = AttendanceSheets.__new__(AttendanceSheets)
        sheets.attendance = Mock()
        local_time = datetime(2026, 10, 13, 9, 30, tzinfo=ZoneInfo("Asia/Almaty"))

        sheets.record_attendance(
            42,
            "Test User",
            None,
            "Выход",
            "проспект Абая, 10, Алматы, Казахстан",
            local_time,
        )

        row = sheets.attendance.append_row.call_args.args[0]
        self.assertEqual(row[0], "13.10.2026 09:30:00 (Астана, UTC+05:00)")
        self.assertEqual(row[5:], ["Выход", "проспект Абая, 10, Алматы, Казахстан"])

    def test_existing_sheet_writes_new_fields_after_legacy_coordinates(self) -> None:
        sheets = AttendanceSheets.__new__(AttendanceSheets)
        sheets.attendance = Mock()
        sheets.has_legacy_coordinate_columns = True
        local_time = datetime(2026, 10, 13, 9, 30, tzinfo=ZoneInfo("Asia/Almaty"))

        sheets.record_attendance(
            42,
            "Test User",
            None,
            "Приход",
            "Алматы, Казахстан",
            local_time,
        )

        row = sheets.attendance.append_row.call_args.args[0]
        self.assertEqual(row[5:7], ["", ""])
        self.assertEqual(row[7:], ["Приход", "Алматы, Казахстан"])


if __name__ == "__main__":
    unittest.main()
