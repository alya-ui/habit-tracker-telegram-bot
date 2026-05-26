from bot.database.db import add_habit, get_habits, mark_done, is_done_today, get_streak, get_stats, get_days_since_creation, get_target_days, get_best_streak
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.filters import CommandStart, Command

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

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    await message.answer(
        "Готово! 🥳 Привычка добавлена!\n\n"
        f"🍀 Название: {data['privychka']}\n"
        f"📆 Дней: {data['dni']}\n"
        f"🕘 Время: {data['vremya']}\n",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Выйти в меню", callback_data="to_menu")]
            ]
        )
    )


async def habits_menu(call: CallbackQuery):
    habits = await get_habits(call.from_user.id)

    if not habits:
        await call.message.answer("У тебя пока нет привычек 😢")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            *[
                [InlineKeyboardButton(text=f"🍀 {name}", callback_data=f"habit_{hid}")]
                for hid, name, _, _ in habits
            ],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu")]
        ]
    )

    await call.message.answer("📋 Твои привычки:", reply_markup=kb)


@router.callback_query(F.data == "my_habits")
async def my_habits(call: CallbackQuery):
    await habits_menu(call)
    await call.answer()

@router.callback_query(F.data == "back_to_list")
async def back(call: CallbackQuery):
    await habits_menu(call)
    await call.answer()


@router.callback_query(F.data.startswith("habit_"))
async def habit_card(call: CallbackQuery):
    habit_id = int(call.data.split("_")[1])

    habits = await get_habits(call.from_user.id)

    habit = next((h for h in habits if h[0] == habit_id), None)

    if not habit:
        await call.answer("Привычка не найдена 😢", show_alert=True)
        return

    _, name, target_days, reminder_time = habit

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✔ Выполнено", callback_data=f"complete_{habit_id}")],
        [InlineKeyboardButton(text="✏ Изменить название", callback_data=f"edit_name_{habit_id}")],
        [InlineKeyboardButton(text="⏰ Изменить время", callback_data=f"edit_time_{habit_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{habit_id}")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu")]
    ])

    await call.message.answer(
        f"🍀 *Привычка:* {name}\n"
        f"🕘 *Напоминание:* {reminder_time}\n"
        f"📆 Цель: {target_days} дней\n\n"
        "Выбери действие:",
        reply_markup=kb,
        parse_mode="Markdown"
    )

    await call.answer()


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


from bot.handlers.start import main_menu

@router.callback_query(F.data == "to_menu")
async def to_menu(call: CallbackQuery):
    await call.message.edit_text(
        "📍 Главное меню\nВыберите действие 👇",
        reply_markup=main_menu
    )
    await call.answer()


@router.message(Command("stats"))
async def stats(message: Message):
    user_id = message.from_user.id
    habits = await get_habits(user_id)
    if not habits:
        await message.answer("У тебя пока нет привычек. Добавь через /add_habit")
        return
    
    text = "📊 *Твоя статистика:*\n\n"
    
    for habit_id, name, target_days, reminder_time in habits:
        stats_data = await get_stats(habit_id)
        best_streak = await get_best_streak(habit_id)
        best = await get_best_streak(habit_id)
        text += (
            f"🍀 *{name}*\n"
            f"📆 Выполнено: {stats_data['done']} из {target_days} дней\n"
            f"📊 Прогресс: {stats_data['percent']}%\n"
            f"🔥 Текущая серия: {stats_data['streak']} дн.\n"
            f"🏆 Рекордная серия: {best} дн.\n"
            f"-------------------\n"
        )
    
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("complete"))
async def complete_choice(message: Message):
    habits = await get_habits(message.from_user.id)
    if not habits:
        await message.answer("У тебя пока нет привычек. Добавь /add_habit")
        return
    keyboard = []
    for hid, name, _, _ in habits:
        keyboard.append([InlineKeyboardButton(text=name, callback_data=f"complete_{hid}")])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("Какую привычку ты выполнил(а) сегодня?", reply_markup=markup)

@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/add_habit - добавить привычку\n"
        "/my_habits - список привычек\n"
        "/complete - отметить выполнение\n"
        "/stats - статистика\n"
        "/help - справка"
    )


