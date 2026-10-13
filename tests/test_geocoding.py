import unittest

from attendance_bot.geocoding import format_place


class FormatPlaceTests(unittest.TestCase):
    def test_includes_street_house_city_and_country(self) -> None:
        address = {
            "road": "проспект Абая",
            "house_number": "10",
            "city": "Алматы",
            "country": "Казахстан",
        }
        self.assertEqual(
            format_place(address),
            "проспект Абая, 10, Алматы, Казахстан",
        )

    def test_falls_back_to_town_and_country(self) -> None:
        self.assertEqual(
            format_place({"town": "Москва", "country": "Россия"}),
            "Москва, Россия",
        )

    def test_reports_unknown_address_without_coordinates(self) -> None:
        self.assertEqual(format_place({}), "Адрес не определен")


if __name__ == "__main__":
    unittest.main()
