from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.database.db import delete_habit

import re

from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

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
    update_habit_name,
    update_habit_days,
    update_habit_time,
)

router = Router()
class dobav_privychku(StatesGroup):
    zhdyom_nazvanie = State()
    zhdyom_dni = State()
    zhdyom_vremya = State()

class EditHabitStates(StatesGroup):
    choosing_habit = State()
    choosing_field = State()

    editing_name = State()
    editing_days = State()
    editing_time = State()

@router.message(Command("add_habit"))
async def add_habit_command(message: Message, state: FSMContext):
    await message.answer(
        "Давай добавим новую привычку! 🌟\n\n"
        "Напиши название привычки"
    )
    await state.set_state(dobav_privychku.zhdyom_nazvanie)
@router.callback_query(F.data == "add_habit")
async def add_habit_button(call: CallbackQuery, state: FSMContext):
    await call.message.answer(
        "Давай добавим новую привычку! 🌟\n\n"
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
        f"📌 Название: {dannye['privychka']}\n"
        f"📅 Количество дней: {dannye['dni']}\n"
        f"🕒 Время напоминаний: {dannye['vremya']}\n"
        "Если хочешь добавить ещё одну привычку, то просто введи /add_habit",
        reply_markup=back_to_menu
    )
    await state.clear()
back_to_menu = InlineKeyboardMarkup(
       inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🏠 В меню",
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
        "✏️ Добавить привычку — создать новую привычку\n"
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
            "У тебя пока нет привычек 😱\n\n"
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
            await callback.message.answer("🌱 Первый день! Отличный старт!",
            reply_markup=back_to_menu)
        elif streak == 3:
            await callback.message.answer("🔥 3 дня! Ты растёшь!",
            reply_markup=back_to_menu)
        elif streak == 5:
            await callback.message.answer("⭐ 5 дней! Горжусь тобой, боец!",
            reply_markup=back_to_menu)
        elif streak == 7:
            await callback.message.answer("🎉 Целая неделя! Ты крут!",
            reply_markup=back_to_menu)
        elif streak == 10:
            await callback.message.answer("🚀 10 дней! Дисциплина — это ты!",
            reply_markup=back_to_menu)
        elif streak == 14:
            await callback.message.answer("🏆 14 дней! Золотой уровень дисциплины!",
            reply_markup=back_to_menu)
        elif streak == 21:
            await callback.message.answer("💪 21 день! Привычка закрепляется!",
            reply_markup=back_to_menu)
        elif streak == 30:
            await callback.message.answer("👑 МЕСЯЦ! Ты невероятен!",
            reply_markup=back_to_menu)
        elif streak > 30 and streak % 5 == 0:
            await callback.message.answer(f"🎯 Месяцы сбудутся, а ты с нами уже {streak} дней! Так держать!",
            reply_markup=back_to_menu)

        if streak == target_days:
            await callback.message.answer(f"🎊 ПОЗДРАВЛЯЮ! Ты выполнил цель в {target_days} дней! Ты молодец!",
            reply_markup=back_to_menu)

    await callback.answer()



@router.callback_query(F.data == "to_menu")
async def to_menu_button(call: CallbackQuery):
    await call.message.edit_text(
        menu_text(),
        reply_markup=main_menu
    )
    await call.answer()

@router.callback_query(F.data == "my_habits")
async def my_habits_button(call: CallbackQuery):
    habits = await get_habits(call.from_user.id)

    if not habits:
        await call.message.answer(
            "У тебя пока нет привычек 😱\n\n"
            "Нажми «Добавить привычку», чтобы создать первую."
        )
        await call.answer()
        return

    keyboard = []

    for habit_id, name, target_days, reminder_time in habits:

        done_today = await is_done_today(habit_id)

        status = "✅" if done_today else "⌛️"

        keyboard.append([
            InlineKeyboardButton(
                text=f"{status} {name}",
                callback_data=f"habit_{habit_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="🏠 В меню",
            callback_data="to_menu"
        )
    ])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await call.message.answer(
        "📋 Твои привычки:",
        reply_markup=markup
    )

    await call.answer()

@router.callback_query(F.data.startswith("habit_"))
async def habit_card(call: CallbackQuery):

    habit_id = int(call.data.split("_")[1])

    habits = await get_habits(call.from_user.id)

    current_habit = None

    for habit in habits:
        if habit[0] == habit_id:
            current_habit = habit
            break

    if not current_habit:
        await call.answer("Привычка не найдена 😢", show_alert=True)
        return

    _, name, target_days, reminder_time = current_habit

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Выполнено",
                    callback_data=f"complete_{habit_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data=f"hstats_{habit_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏ Изменить",
                    callback_data=f"editmenu_{habit_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"delask_{habit_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅ Назад",
                    callback_data="my_habits"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 В меню",
                    callback_data="to_menu"
                )
            ]
        ]
    )

    await call.message.answer(
        f"📌 *Привычка:* {name}\n"
        f"🎯 *Цель:* {target_days} дней\n"
        f"🕒 *Напоминание:* {reminder_time}",
        reply_markup=kb,
        parse_mode="Markdown"
    )

    await call.answer()


@router.callback_query(F.data.startswith("hstats_"))
async def habit_stats_button(call: CallbackQuery):
    habit_id = int(call.data.split("_")[1])

    stats_data = await get_stats(habit_id)
    best = await get_best_streak(habit_id)

    await call.message.answer(
        "📊 Статистика привычки\n\n"
        f"✅ Выполнено: {stats_data['done']}\n"
        f"📈 Прогресс: {stats_data['percent']}%\n"
        f"🔥 Текущая серия: {stats_data['streak']} дн.\n"
        f"🏆 Рекордная серия: {best} дн."
    )

    await call.answer()

@router.callback_query(F.data.startswith("editmenu_"))
async def edit_menu(call: CallbackQuery, state: FSMContext):
    habit_id = int(call.data.split("_")[1])

    await state.clear()
    await state.update_data(habit_id=habit_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Название", callback_data="edit_name")],
        [InlineKeyboardButton(text="📅 Дни", callback_data="edit_days")],
        [InlineKeyboardButton(text="⏰ Время", callback_data="edit_time")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"habit_{habit_id}")]
    ])

    await call.message.edit_text("✏ Что хочешь изменить?", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data == "edit_name")
async def edit_name_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(EditHabitStates.editing_name)

    await call.message.edit_text(
        "📝 Введи новое название привычки:"
    )
    await call.answer()

@router.message(EditHabitStates.editing_name)
async def edit_name_save(message: Message, state: FSMContext):
    data = await state.get_data()
    habit_id = data.get("habit_id")

    if not habit_id:
        await message.answer("❌ Ошибка состояния. Попробуй снова.")
        await state.clear()
        return

    name = message.text.strip()

    if len(name) < 2:
        await message.answer("❌ Минимум 2 символа")
        return

    if len(name) > 50:
        await message.answer("❌ Максимум 50 символов")
        return

    await update_habit_name(habit_id, message.from_user.id, name)

    await message.answer("✅ Название обновлено")
    await state.clear()

@router.callback_query(F.data == "edit_days")
async def edit_days_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(EditHabitStates.editing_days)

    await call.message.edit_text("📅 Введи новое количество дней:")
    await call.answer()

@router.message(EditHabitStates.editing_days)
async def edit_days_save(message: Message, state: FSMContext):
    data = await state.get_data()
    habit_id = data.get("habit_id")

    if not habit_id:
        await message.answer("❌ Ошибка состояния")
        await state.clear()
        return

    if not message.text.isdigit():
        await message.answer("❌ Введи число")
        return

    new_days = int(message.text)

    if new_days <= 0:
        await message.answer("❌ Должно быть больше 0")
        return

    stats = await get_stats(habit_id)
    done = stats["done"]

    if new_days < done:
        await message.answer(f"❌ Уже выполнено: {done}")
        return

    await update_habit_days(habit_id, message.from_user.id, new_days)

    await message.answer("✅ Цель обновлена")
    await state.clear()

@router.callback_query(F.data == "edit_time")
async def edit_time_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(EditHabitStates.editing_time)

    await call.message.edit_text("⏰ Введи время (ЧЧ:ММ):")
    await call.answer()

@router.message(EditHabitStates.editing_time)
async def edit_time_save(message: Message, state: FSMContext):
    data = await state.get_data()
    habit_id = data.get("habit_id")

    if not habit_id:
        await message.answer("❌ Ошибка состояния")
        await state.clear()
        return

    text = message.text.strip()

    if not re.match(r"^\d{2}:\d{2}$", text):
        await message.answer("❌ Формат ЧЧ:ММ")
        return

    h, m = map(int, text.split(":"))

    if h > 23 or m > 59:
        await message.answer("❌ Неверное время")
        return

    await update_habit_time(habit_id, message.from_user.id, text)

    await message.answer("✅ Время обновлено")
    await state.clear()

@router.callback_query(F.data.startswith("delask_"))
async def delete_confirm(call: CallbackQuery):
    habit_id = int(call.data.split("_")[1])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="❌ Удалить",
                callback_data=f"delete_yes_{habit_id}"
            ),
            InlineKeyboardButton(
                text="⬅ Оставить",
                callback_data=f"habit_{habit_id}"
            )
        ]
    ])

    await call.message.edit_text(
        "❓ Точно удалить привычку?",
        reply_markup=kb
    )
    await call.answer()


@router.callback_query(F.data.startswith("delete_yes_"))
async def delete_final(call: CallbackQuery):
    habit_id = int(call.data.split("_")[2])

    success = await delete_habit(habit_id, call.from_user.id)

    if success:
        await call.message.edit_text("🗑 Привычка удалена")
    else:
        await call.message.edit_text("❌ Не удалось удалить")

    await call.answer()
