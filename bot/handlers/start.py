from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

router = Router()

start_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🚀 Начать", callback_data="start_app")]
])

main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🍀 Добавить привычку", callback_data="add_habit")],
    [InlineKeyboardButton(text="📋 Мои привычки", callback_data="my_habits")]
])

@router.message(CommandStart())
async def start_command(message: Message):
    await message.answer(
        "Привет! 👋\n\n"
        "Я бот для формирования полезных привычек 💪\n\n"
        "Я помогу тебе выстроить систему, которая реально работает 🚀\n\n"
        "Нажми 'Начать', чтобы перейти в меню 👇",
        reply_markup=start_menu
    )

@router.callback_query(F.data == "start_app")
async def start_app(call: CallbackQuery):
    await call.message.answer(
        "Отлично! 🔥\n\n"
        "Добро пожаловать в главное меню 👇",
        reply_markup=main_menu
    )
    await call.answer()

@router.callback_query(F.data == "add_habit")
async def add_habit_callback(call: CallbackQuery, state: FSMContext):
    from bot.handlers.habits import start_add_habit
    await start_add_habit(call, state)
    await call.answer()

@router.callback_query(F.data == "my_habits")
async def my_habits_callback(call: CallbackQuery):
    from bot.handlers.habits import my_habits
    await my_habits(call.message)
    await call.answer()