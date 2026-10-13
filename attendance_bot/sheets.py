from datetime import datetime, timezone

import gspread
from gspread.utils import rowcol_to_a1

from attendance_bot.config import Settings
from attendance_bot.time_format import format_local_time

ATTENDANCE_HEADERS = [
    "Время (локальное)",
    "Время (UTC)",
    "Telegram ID",
    "Имя",
    "Username",
    "Тип отметки",
    "Местоположение",
]
USER_HEADERS = ["Telegram ID", "Имя", "Username", "Активен", "Зарегистрирован"]


class AttendanceSheets:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.attendance = None
        self.users = None
        self.has_legacy_coordinate_columns = False

    def initialize(self) -> None:
        client = gspread.service_account(filename=self.settings.google_credentials_file)
        spreadsheet = client.open_by_key(self.settings.spreadsheet_id)
        self.attendance = self._get_or_create_worksheet(
            spreadsheet, self.settings.attendance_worksheet
        )
        self.users = self._get_or_create_worksheet(spreadsheet, self.settings.users_worksheet)
        existing_headers = self.attendance.row_values(1)
        self.has_legacy_coordinate_columns = any(
            header in existing_headers
            for header in (
                "Широта",
                "Долгота",
                "Широта (старые записи)",
                "Долгота (старые записи)",
            )
        )
        self._ensure_headers(self.attendance, ATTENDANCE_HEADERS)
        self._ensure_headers(self.users, USER_HEADERS)

    @staticmethod
    def _get_or_create_worksheet(spreadsheet, title: str):
        try:
            return spreadsheet.worksheet(title)
        except gspread.WorksheetNotFound:
            return spreadsheet.add_worksheet(title=title, rows=1000, cols=10)

    @staticmethod
    def _ensure_headers(worksheet, headers: list[str]) -> None:
        existing = worksheet.row_values(1)
        if not existing:
            worksheet.update(range_name="A1", values=[headers], value_input_option="RAW")
            return

        updated = list(existing)
        for old_header, archived_header in (
            ("Широта", "Широта (старые записи)"),
            ("Долгота", "Долгота (старые записи)"),
        ):
            if old_header in updated and archived_header not in updated:
                updated[updated.index(old_header)] = archived_header
        for header in headers:
            if header not in updated:
                updated.append(header)

        if updated != existing:
            missing_columns = len(updated) - worksheet.col_count
            if missing_columns > 0:
                worksheet.add_cols(missing_columns)
            worksheet.update(
                range_name=f"A1:{rowcol_to_a1(1, len(updated))}",
                values=[updated],
                value_input_option="RAW",
            )

    def register_user(self, user_id: int, name: str, username: str | None) -> None:
        worksheet = self._users()
        existing_ids = worksheet.col_values(1)
        values = [str(user_id), name, username or "", "TRUE", datetime.now(timezone.utc).isoformat()]
        try:
            row = existing_ids.index(str(user_id)) + 1
        except ValueError:
            worksheet.append_row(values, value_input_option="RAW")
        else:
            worksheet.update(
                range_name=f"A{row}:E{row}", values=[values], value_input_option="RAW"
            )

    def active_users(self) -> list[dict[str, str]]:
        records = self._users().get_all_records()
        return [
            record
            for record in records
            if str(record.get("Активен", "")).strip().upper() == "TRUE"
        ]

    def record_attendance(
        self,
        user_id: int,
        name: str,
        username: str | None,
        event_type: str,
        place: str,
        local_time: datetime,
    ) -> None:
        utc_time = local_time.astimezone(timezone.utc)
        row = [
            format_local_time(local_time),
            utc_time.isoformat(timespec="seconds"),
            str(user_id),
            name,
            username or "",
        ]
        if getattr(self, "has_legacy_coordinate_columns", False):
            row.extend(["", ""])
        row.extend([event_type, place])
        self._attendance().append_row(row, value_input_option="RAW")

    def last_attendance(self, user_id: int) -> dict | None:
        records = self._attendance().get_all_records()
        for record in reversed(records):
            if str(record.get("Telegram ID", "")) == str(user_id):
                return record
        return None

    def _attendance(self):
        if self.attendance is None:
            raise RuntimeError("Google Sheets has not been initialized")
        return self.attendance

    def _users(self):
        if self.users is None:
            raise RuntimeError("Google Sheets has not been initialized")
        return self.users
