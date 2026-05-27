from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


start_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Вперёд", callback_data="start_app")]
    ]
)


main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🍀 Добавить привычку", callback_data="add_habit")],
        [InlineKeyboardButton(text="📋 Мои привычки", callback_data="my_habits")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ]
)

def menu_text():
    return "📍 Вы находитесь в главном меню\nВыберите действие 👇"