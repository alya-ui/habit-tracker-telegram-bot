from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command

from bot.database.db import add_habit, get_habits,  mark_done, get_streak, get_target_days, get_days_since_creation, update_habit_name, update_habit_days, update_habit_time, delete_habit

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

@router.callback_query(F.data.startswith("complete_"))
async def complete_callback(callback: CallbackQuery):
    habit_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    habits = await get_habits(user_id)
    if habit_id not in [h[0] for h in habits]:
        await callback.answer("Это не твоя привычка!", show_alert=True)
        return

    await mark_done(habit_id)
    streak = await get_streak(habit_id)

    await callback.message.edit_text(f"Отлично! Привычка отмечена. Текущая серия: {streak} дн.")

    target_days = await get_target_days(habit_id)
    
    if streak <= target_days:
        if streak == 1:
            await callback.message.answer("🌱 Первый день! Отличный старт!")
        elif streak == 3:
            await callback.message.answer("🔥 3 дня! Ты растёшь!")
        elif streak == 5:
            await callback.message.answer("⭐ 5 дней! Горжусь тобой, боец!")
        elif streak == 7:
            await callback.message.answer("🌟 Целая неделя! Ты крут!")
        elif streak == 10:
            await callback.message.answer("🎉 10 дней! Дисциплина — это ты!")
        elif streak == 14:
            await callback.message.answer("💎 14 дней! Золотой уровень дисциплины!")
        elif streak == 21:
            await callback.message.answer("💪 21 день! Привычка закрепляется!")
        elif streak == 30:
            await callback.message.answer("🏆 МЕСЯЦ! Ты невероятен!")
        elif streak > 30 and streak % 5 == 0:
            await callback.message.answer(f"🎯 Мечты сбудутся, а ты с нами уже {streak} дней! Так держать!")
        
        if streak == target_days:
            await callback.message.answer(f"🏆 ПОЗДРАВЛЯЮ! Ты выполнил цель в {target_days} дней! Ты молодец!")

    await callback.answer()

@router.message(Command("edit_habit"))
async def edit_habit_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    habits = await get_habits(user_id)
    
    if not habits:
        await message.answer("📭 У тебя пока нет привычек. Добавь через /add_habit")
        return
    
    keyboard = []
    for habit_id, name, target_days, reminder_time in habits:
        keyboard.append([InlineKeyboardButton(
            text=f"✏️ {name} (цель: {target_days} дн.)",
            callback_data=f"edit_{habit_id}"
        )])
    
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("📝 Какую привычку хочешь изменить?", reply_markup=markup)
    await state.set_state(EditHabitStates.choosing_habit)


@router.callback_query(EditHabitStates.choosing_habit, F.data.startswith("edit_"))
async def edit_habit_choose_field(callback: CallbackQuery, state: FSMContext):
    habit_id = int(callback.data.split("_")[1])
    
    await state.update_data(habit_id=habit_id)
    
    from bot.database.db import get_habit_by_id
    habit = await get_habit_by_id(habit_id, callback.from_user.id)
    
    if not habit:
        await callback.message.answer("❌ Привычка не найдена")
        await state.clear()
        await callback.answer()
        return
    
    await state.update_data(habit_name=habit['name'])
    
    keyboard = [
        [InlineKeyboardButton(text="📝 Изменить название", callback_data="field_name")],
        [InlineKeyboardButton(text="📆 Изменить количество дней", callback_data="field_days")],
        [InlineKeyboardButton(text="⏰ Изменить время напоминания", callback_data="field_time")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="field_cancel")]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        f"🍀 *{habit['name']}*\n"
        f"📆 Цель: {habit['target_days']} дней\n"
        f"⏰ Время: {habit['reminder_time'] or 'не установлено'}\n\n"
        f"Что хочешь изменить?",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    await state.set_state(EditHabitStates.choosing_field)
    await callback.answer()


@router.callback_query(EditHabitStates.choosing_field, F.data.startswith("field_"))
async def edit_habit_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split("_")[1]
    
    if field == "cancel":
        await callback.message.edit_text("❌ Изменение отменено")
        await state.clear()
        await callback.answer()
        return
    
    await state.update_data(edit_field=field)
    
    if field == "name":
        await callback.message.edit_text("📝 Введи новое название привычки:")
        await state.set_state(EditHabitStates.editing_name)
    
    elif field == "days":
        await callback.message.edit_text("📆 Введи новое количество дней (целое число):")
        await state.set_state(EditHabitStates.editing_days)
    
    elif field == "time":
        await callback.message.edit_text(
            "⏰ Введи новое время напоминания в формате ЧЧ:ММ\n"

        )
        await state.set_state(EditHabitStates.editing_time)
    
    await callback.answer()


@router.message(EditHabitStates.editing_name)
async def edit_habit_name(message: Message, state: FSMContext):
    new_name = message.text.strip()
    
    data = await state.get_data()
    habit_id = data["habit_id"]
    
    from bot.database.db import update_habit_name
    await update_habit_name(habit_id, new_name)
    
    await message.answer(f"✅ Название привычки изменено на *{new_name}*", parse_mode="Markdown")
    await state.clear()


@router.message(EditHabitStates.editing_days)
async def edit_habit_days(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введи число. Например: 30")
        return
    
    new_days = int(message.text)
    
    if new_days <= 0:
        await message.answer("❌ Количество дней должно быть больше 0")
        return
    
    data = await state.get_data()
    habit_id = data["habit_id"]
    
    from bot.database.db import update_habit_days
    await update_habit_days(habit_id, new_days)
    
    await message.answer(f"✅ Цель изменена на *{new_days}* дней", parse_mode="Markdown")
    await state.clear()


@router.message(EditHabitStates.editing_time)
async def edit_habit_time(message: Message, state: FSMContext):
    new_time = message.text.strip()
    
    data = await state.get_data()
    habit_id = data["habit_id"]
    
    from bot.database.db import update_habit_time
 
    if len(new_time) != 5 or new_time[2] != ":":
        await message.answer("❌ Неверный формат. Используй ЧЧ:ММ")
        return
    
    hours, minutes = new_time.split(":")
    if not (hours.isdigit() and minutes.isdigit()):
        await message.answer("❌ Неверный формат. Используй ЧЧ:ММ")
        return
    
    hours = int(hours)
    minutes = int(minutes)
    
    if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
        await message.answer("❌ Время должно быть от 00:00 до 23:59")
        return
    
    await update_habit_time(habit_id, new_time)
    await message.answer(f"✅ Время напоминания изменено на *{new_time}*", parse_mode="Markdown")
    await state.clear()

@router.message(Command("delete_habit"))
async def delete_habit_start(message: Message):
    user_id = message.from_user.id
    habits = await get_habits(user_id)
    
    if not habits:
        await message.answer("📭 У тебя пока нет привычек. Добавь через /add_habit")
        return
    
    keyboard = []
    for habit_id, name, target_days, reminder_time in habits:
        keyboard.append([InlineKeyboardButton(
            text=f"❌ {name} (цель: {target_days} дн.)",
            callback_data=f"delete_{habit_id}"
        )])
    
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="delete_cancel")])
    
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("🗑️ Какую привычку хочешь удалить?", reply_markup=markup)


@router.callback_query(F.data.startswith("delete_"))
async def delete_habit_confirm(callback: CallbackQuery):
    data = callback.data
    
    if data == "delete_cancel":
        await callback.message.edit_text("❌ Удаление отменено")
        await callback.answer()
        return
    
    habit_id = int(data.split("_")[1])
    
    from bot.database.db import delete_habit
    success = await delete_habit(habit_id, callback.from_user.id)
    
    if success:
        await callback.message.edit_text("✅ Привычка успешно удалена")
    else:
        await callback.message.edit_text("❌ Привычка не найдена или уже удалена")
    
    await callback.answer()