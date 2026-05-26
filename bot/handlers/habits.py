from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.inline import main_menu, menu_text
from bot.database.db import (
    add_habit,
    get_habits,
    mark_done,
    is_done_today,
    get_streak,
    get_stats,
    get_target_days,
    get_best_streak,
)
router = Router()
class dobav_privychku(StatesGroup):
    zhdyom_nazvanie = State()
    zhdyom_dni = State()
    zhdyom_vremya = State()
@router.message(Command("add_habit"))


async def add_habit_command(message: Message, state: FSMContext):
    await message.answer(
        "Давай добавим новую привычку! 🍀\n\n"
        "Напиши название привычки"
    )
    await state.set_state(dobav_privychku.zhdyom_nazvanie)


@router.message(dobav_privychku.zhdyom_nazvanie)


async def poluchit_nazvanie(message: Message, state: FSMContext):
    privychka = message.text.strip()
    if len(privychka) < 2:
        await message.answer("Название слишком короткое 😢 Попробуй ещё раз!")
        return
    await state.update_data(privychka=privychka)
    await message.answer(
        "Хороший выбор!\n\n"
        "Теперь напиши, сколько дней ты хочешь выполнять привычку\n"
    )
    await state.set_state(dobav_privychku.zhdyom_dni)


@router.message(dobav_privychku.zhdyom_dni)


async def poluchit_dni(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, напиши число. Например: 17")
        return
    dni = int(message.text)
    if dni <= 0:
        await message.answer("Количество дней должно быть больше 0")
        return
    await state.update_data(dni=dni)
    await message.answer(
        "Замечательно!\n\n"
        "Осталось совсем чуть-чуть! Напиши время напоминания в формате ЧЧ:ММ\n"
        "Например: 09:15"
    )
    await state.set_state(dobav_privychku.zhdyom_vremya)


@router.message(dobav_privychku.zhdyom_vremya)


async def poluchit_vremya(message: Message, state: FSMContext):
    vremya = message.text.strip()
    if len(vremya) != 5 or vremya[2] != ":":
        await message.answer("Время должно быть в формате ЧЧ:ММ. Например: 10:24")
        return
    chasy, minuty = vremya.split(":")
    chasy = int(chasy)
    minuty = int(minuty)
    if chasy < 0 or chasy > 23 or minuty < 0 or minuty > 59:
        await message.answer("Некорректное время 😢 Напиши время от 00:00 до 23:59")
        return
    await state.update_data(vremya=vremya)
    dannye = await state.get_data()
    await add_habit(
    user_id=message.from_user.id,
    name=dannye["privychka"],
    target_days=dannye["dni"],
    reminder_time=dannye["vremya"]
)
    await message.answer(
        "Готово! 🥳 Привычка добавлена!\n\n"
        f"👀 Название: {dannye['privychka']}\n"
        f"📆 Количество дней: {dannye['dni']}\n"
        f"🕘 Время напоминаний: {dannye['vremya']}\n"
        "Если хочешь добавить ещё одну привычку, то просто введи /add_habit"
    )
    await state.clear()
back_to_menu = InlineKeyboardMarkup(
       inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔙 В меню",
                callback_data="to_menu"
            )
        ]
    ]
)
@router.callback_query(F.data == "help")
async def help_button(call: CallbackQuery):
    await call.message.edit_text(
        "❓ Помощь\n\n"
        "Что умеет бот:\n\n"
        "☘️ Добавить привычку — создать новую привычку\n"
        "📋 Мои привычки — посмотреть список привычек\n"
        "📊 Статистика — посмотреть прогресс\n\n"
        "Также можно использовать команды:\n"
        "/start — запустить бота\n"
        "/add_habit — добавить привычку\n\n"
        "Если хочешь вернуться назад, нажми кнопку ниже 👇",
        reply_markup=back_to_menu
    )
    await call.answer()
@router.callback_query(F.data == "stats")
async def stats_button(call: CallbackQuery):
    habits = await get_habits(call.from_user.id)
    if not habits:
        await call.message.edit_text(
            "У тебя пока нет привычек 🌱\n\n"
            "Сначала добавь привычку через кнопку «Добавить привычку».",
            reply_markup=back_to_menu
        )
        await call.answer()
        return
    text = "📊 Твоя статистика\n\n"
    for habit_id, name, target_days, reminder_time in habits:
        stats_data = await get_stats(habit_id)
        best = await get_best_streak(habit_id)
        text += (
            f"🌱 {name}\n"
            f"✅ Выполнено: {stats_data['done']} из {target_days} дней\n"
            f"📈 Прогресс: {stats_data['percent']}%\n"
            f"🔥 Текущая серия: {stats_data['streak']} дн.\n"
            f"🏆 Рекордная серия: {best} дн.\n"
            f"⏰ Напоминание: {reminder_time}\n\n"
        )
    await call.message.edit_text(
        text,
        reply_markup=back_to_menu
    )
    await call.answer()
@router.callback_query(F.data == "to_menu")
async def to_menu_button(call: CallbackQuery):
    await call.message.edit_text(
        menu_text(),
        reply_markup=main_menu
    )
    await call.answer()