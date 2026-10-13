from datetime import datetime


def format_local_time(value: datetime) -> str:
    timezone_key = getattr(value.tzinfo, "key", "")
    timezone_label = "Астана" if timezone_key == "Asia/Almaty" else timezone_key
    if not timezone_label:
        timezone_label = value.tzname() or "местное время"

    offset = value.strftime("%z")
    if len(offset) == 5:
        offset = f"{offset[:3]}:{offset[3:]}"
    return f"{value:%d.%m.%Y %H:%M:%S} ({timezone_label}, UTC{offset})"
