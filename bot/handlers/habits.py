from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
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
    await message.answer(
        "Готово! 🥳 Привычка добавлена!\n\n"
        f"👀 Название: {dannye['privychka']}\n"
        f"📆 Количество дней: {dannye['dni']}\n"
        f"🕘 Время напоминаний: {dannye['vremya']}\n"
        "Если хочешь добавить ещё одну привычку, то просто введи /add_habit"
    )
    await state.clear()