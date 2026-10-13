from dataclasses import dataclass
from datetime import time
import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv


def parse_reminder_times(value: str) -> list[time]:
    """Parse comma-separated local times in HH:MM format."""
    parsed: list[time] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            hour_text, minute_text = item.split(":", maxsplit=1)
            parsed.append(time(hour=int(hour_text), minute=int(minute_text)))
        except (ValueError, TypeError) as error:
            raise ValueError(f"Invalid reminder time {item!r}; expected HH:MM") from error
    if not parsed:
        raise ValueError("At least one reminder time is required")
    return parsed


@dataclass(frozen=True)
class Settings:
    bot_token: str
    spreadsheet_id: str
    google_credentials_file: str
    timezone: ZoneInfo
    reminder_times: list[time]
    attendance_worksheet: str
    users_worksheet: str


def load_settings() -> Settings:
    load_dotenv()
    required = ("BOT_TOKEN", "GOOGLE_SHEETS_ID", "GOOGLE_CREDENTIALS_FILE")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    timezone_name = os.getenv("TIMEZONE", "Asia/Almaty")
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as error:
        raise ValueError(f"Unknown TIMEZONE: {timezone_name}") from error

    return Settings(
        bot_token=os.environ["BOT_TOKEN"],
        spreadsheet_id=os.environ["GOOGLE_SHEETS_ID"],
        google_credentials_file=os.environ["GOOGLE_CREDENTIALS_FILE"],
        timezone=timezone,
        reminder_times=parse_reminder_times(os.getenv("REMINDER_TIMES", "09:00,18:00")),
        attendance_worksheet=os.getenv("ATTENDANCE_WORKSHEET", "Attendance"),
        users_worksheet=os.getenv("USERS_WORKSHEET", "Users"),
    )
