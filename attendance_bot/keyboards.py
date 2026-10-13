from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

MARK_BUTTON = "Отметиться"
DEPARTURE_BUTTON = "Отметить выход"
LAST_BUTTON = "Моя последняя отметка"
HELP_BUTTON = "Помощь"
LOCATION_BUTTON = "Отправить геопозицию"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MARK_BUTTON), KeyboardButton(text=DEPARTURE_BUTTON)],
            [KeyboardButton(text=LAST_BUTTON)],
            [KeyboardButton(text=HELP_BUTTON)],
        ],
        resize_keyboard=True,
    )


def location_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=LOCATION_BUTTON, request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
