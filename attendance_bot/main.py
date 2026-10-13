import asyncio
import logging
from datetime import datetime
from html import escape

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from attendance_bot.config import Settings, load_settings
from attendance_bot.keyboards import (
    DEPARTURE_BUTTON,
    HELP_BUTTON,
    LAST_BUTTON,
    LOCATION_BUTTON,
    MARK_BUTTON,
    location_menu,
    main_menu,
)
from attendance_bot.geocoding import ReverseGeocoder
from attendance_bot.sheets import AttendanceSheets
from attendance_bot.time_format import format_local_time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class AttendanceFlow(StatesGroup):
    arrival = State()
    departure = State()


async def send_reminders(bot: Bot, sheets: AttendanceSheets) -> None:
    try:
        users = await asyncio.to_thread(sheets.active_users)
    except Exception:
        logger.exception("Unable to load registered users for reminders")
        return

    for user in users:
        try:
            await bot.send_message(
                chat_id=int(user["Telegram ID"]),
                text="Пора отметить посещаемость: выберите приход или выход в меню.",
                reply_markup=main_menu(),
            )
        except Exception:
            logger.exception("Unable to send reminder to Telegram user %s", user.get("Telegram ID"))


def create_dispatcher(settings: Settings, sheets: AttendanceSheets) -> Dispatcher:
    router = Router()
    geocoder = ReverseGeocoder()

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        if message.from_user is None or message.chat.type != "private":
            return
        user = message.from_user
        name = user.full_name
        try:
            await asyncio.to_thread(sheets.register_user, user.id, name, user.username)
        except Exception:
            logger.exception("Unable to register Telegram user %s", user.id)
            await message.answer("Не удалось подключиться к таблице. Попробуйте позже.")
            return
        await message.answer(
            f"Здравствуйте, {escape(name)}! Выберите действие в меню.\n\n"
            "При отправке геопозиции адрес и время сохраняются в таблице. "
            "Координаты передаются OpenStreetMap для определения адреса.",
            reply_markup=main_menu(),
        )

    @router.message(F.text == MARK_BUTTON)
    async def mark_attendance(message: Message, state: FSMContext) -> None:
        await state.set_state(AttendanceFlow.arrival)
        await message.answer(
            "Чтобы отметить приход, отправьте текущую геопозицию кнопкой ниже.",
            reply_markup=location_menu(),
        )

    @router.message(F.text == DEPARTURE_BUTTON)
    async def mark_departure(message: Message, state: FSMContext) -> None:
        await state.set_state(AttendanceFlow.departure)
        await message.answer(
            "Чтобы отметить выход, отправьте текущую геопозицию кнопкой ниже.",
            reply_markup=location_menu(),
        )

    @router.message(F.location)
    async def receive_location(message: Message, state: FSMContext) -> None:
        if message.from_user is None or message.chat.type != "private":
            return
        current_state = await state.get_state()
        if current_state not in (AttendanceFlow.arrival.state, AttendanceFlow.departure.state):
            await message.answer("Сначала выберите «Отметиться» или «Отметить выход».", reply_markup=main_menu())
            return

        event_type = "Выход" if current_state == AttendanceFlow.departure.state else "Приход"
        location = message.location
        local_time = datetime.now(settings.timezone)
        try:
            place = await asyncio.to_thread(
                geocoder.resolve, location.latitude, location.longitude
            )
        except Exception:
            logger.exception("Unable to resolve location for Telegram user %s", message.from_user.id)
            place = "Адрес не определен"
        if place == "Адрес не определен":
            await message.answer(
                "Не удалось определить адрес по геопозиции. Отметка не сохранена; "
                "попробуйте отправить геопозицию еще раз.",
                reply_markup=location_menu(),
            )
            return
        try:
            await asyncio.to_thread(
                sheets.record_attendance,
                message.from_user.id,
                message.from_user.full_name,
                message.from_user.username,
                event_type,
                place,
                local_time,
            )
        except Exception:
            logger.exception("Unable to save attendance for Telegram user %s", message.from_user.id)
            await message.answer(
                "Не удалось сохранить отметку. Попробуйте отправить геопозицию еще раз.",
                reply_markup=main_menu(),
            )
            return
        await state.clear()
        await message.answer(
            f"{event_type} отмечен.\n"
            f"Время: {format_local_time(local_time)}\n"
            f"Место: {place}",
            reply_markup=main_menu(),
        )

    @router.message(F.text == LAST_BUTTON)
    async def last_attendance(message: Message) -> None:
        if message.from_user is None:
            return
        try:
            record = await asyncio.to_thread(sheets.last_attendance, message.from_user.id)
        except Exception:
            logger.exception("Unable to read attendance for Telegram user %s", message.from_user.id)
            await message.answer("Не удалось получить отметку из таблицы.", reply_markup=main_menu())
            return
        if record is None:
            await message.answer("У вас пока нет отметок.", reply_markup=main_menu())
            return
        await message.answer(
            f"Последнее событие: {record.get('Тип отметки', 'Отметка')}\n"
            f"Время: {record.get('Время (локальное)', 'не указано')}\n"
            f"Место: {record.get('Местоположение', 'не указано')}",
            reply_markup=main_menu(),
        )

    @router.message(F.text == HELP_BUTTON)
    async def help_message(message: Message) -> None:
        await message.answer(
            "Для прихода нажмите «Отметиться», для ухода — «Отметить выход», затем "
            "отправьте геопозицию. В таблицу попадут время Астаны, тип события и адрес.",
            reply_markup=main_menu(),
        )

    @router.message(F.text == LOCATION_BUTTON)
    async def location_button_help(message: Message) -> None:
        await message.answer("Нажмите кнопку отправки геопозиции в меню Telegram.")

    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(router)
    return dispatcher


async def run_bot(settings: Settings) -> None:
    sheets = AttendanceSheets(settings)
    await asyncio.to_thread(sheets.initialize)

    bot = Bot(token=settings.bot_token)
    dispatcher = create_dispatcher(settings, sheets)
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    for reminder_time in settings.reminder_times:
        scheduler.add_job(
            send_reminders,
            trigger="cron",
            hour=reminder_time.hour,
            minute=reminder_time.minute,
            args=[bot, sheets],
            id=f"reminder-{reminder_time.hour:02d}-{reminder_time.minute:02d}",
            replace_existing=True,
        )
    scheduler.start()
    logger.info("Bot started; reminders configured for %s", settings.reminder_times)
    try:
        await dispatcher.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


def main() -> None:
    try:
        settings = load_settings()
        asyncio.run(run_bot(settings))
    except (ValueError, OSError) as error:
        logger.error("Configuration/startup error: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
