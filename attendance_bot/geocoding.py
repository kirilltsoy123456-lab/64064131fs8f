from collections.abc import Mapping


def format_place(address: Mapping[str, str]) -> str:
    road = (
        address.get("road")
        or address.get("pedestrian")
        or address.get("residential")
        or address.get("neighbourhood")
    )
    house_number = address.get("house_number")
    street_address = ", ".join(part for part in (road, house_number) if part)
    locality = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("municipality")
        or address.get("county")
    )
    parts = [street_address, locality, address.get("country", "")]
    return ", ".join(dict.fromkeys(part for part in parts if part)) or "Адрес не определен"


class ReverseGeocoder:
    def __init__(self) -> None:
        from geopy.extra.rate_limiter import RateLimiter
        from geopy.geocoders import Nominatim

        geolocator = Nominatim(user_agent="telegram_attendance_bot", timeout=10)
        self._reverse = RateLimiter(
            geolocator.reverse,
            min_delay_seconds=1,
            max_retries=1,
            error_wait_seconds=2,
            swallow_exceptions=True,
            return_value_on_exception=None,
        )

    def resolve(self, latitude: float, longitude: float) -> str:
        result = self._reverse(
            (latitude, longitude),
            language="ru",
            zoom=18,
            addressdetails=True,
        )
        if result is None:
            return "Адрес не определен"
        return format_place(result.raw.get("address", {}))
