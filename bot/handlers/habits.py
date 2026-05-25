from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.database.db import add_habit, get_habits

router = Router()

class dobav_privychku(StatesGroup):
    zhdyom_nazvanie = State()
    zhdyom_dni = State()
    zhdyom_vremya = State()

@router.callback_query(F.data == "add_habit")
async def start_add_habit(call: CallbackQuery, state: FSMContext):
    await call.message.answer(
        "Давай добавим новую привычку! 🍀\n\n"
        "Напиши название привычки"
    )
    await state.set_state(dobav_privychku.zhdyom_nazvanie)
    await call.answer()

@router.message(dobav_privychku.zhdyom_nazvanie)
async def poluchit_nazvanie(message: Message, state: FSMContext):
    privychka = message.text.strip()

    if len(privychka) < 2:
        await message.answer("Название слишком короткое 😢 Попробуй ещё раз!")
        return

    await state.update_data(privychka=privychka)

    await message.answer(
        "Хороший выбор!\n\n"
        "Теперь напиши, сколько дней ты хочешь выполнять привычку"
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
        "Отлично! 🔥\n\n"
        "Теперь напиши время напоминания в формате ЧЧ:ММ\n"
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
        await message.answer("Некорректное время 😢 Напиши от 00:00 до 23:59")
        return

    await state.update_data(vremya=vremya)
    data = await state.get_data()

    await add_habit(
        user_id=message.from_user.id,
        name=data["privychka"],
        target_days=data["dni"],
        reminder_time=data["vremya"]
    )

    await message.answer(
        "Готово! 🥳 Привычка добавлена!\n\n"
        f"👀 Название: {data['privychka']}\n"
        f"📆 Количество дней: {data['dni']}\n"
        f"🕘 Время: {data['vremya']}\n"
    )

    await state.clear()

@router.message(Command("my_habits"))
async def my_habits(message: Message):
    habits = await get_habits(message.from_user.id)

    if not habits:
        await message.answer("У тебя пока нет привычек 😢")
        return

    text = "📋 Твои привычки:\n\n"

    for habit_id, name, target_days, reminder_time in habits:
        text += (
            f"🍀 {name}\n"
            f"📆 {target_days} дней\n"
            f"⏰ {reminder_time}\n"
            f"-------------------\n"
        )

    await message.answer(text)
