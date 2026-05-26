from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import start_menu, main_menu

router = Router()


@router.message(CommandStart())
async def start_command(message: Message):
    await message.answer(
        "Привет! 👋\n\n"
        "Я бот для формирования полезных привычек 💪\n\n"
        "Я помогу тебе:\n"
        "• создавать привычки 🍀\n"
        "• отслеживать прогресс 📊\n"
        "• сохранять серию дней 🔥\n"
        "• не забывать о важных делах ⏰\n\n"
        "Готов начать? 🚀",
        reply_markup=start_menu
    )


@router.callback_query(F.data == "start_app")
async def start_app(call: CallbackQuery):
    await call.message.answer(
        "Добро пожаловать в главное меню 👇",
        reply_markup=main_menu
    )
    await call.answer()