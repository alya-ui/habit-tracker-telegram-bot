from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
router = Router()
@router.message(CommandStart())
async def start_command(message: Message):
    await message.answer(
        "Привет! 👋 \n\n"
        "Я бот для отслеживания привычек!\n\n"
        "Я помогу тебе:\n"
        "💫 добавить полезные привычки в твою жизнь\n"
        "💫 не забывать о них\n"
        "💫 следить за прогрессом\n"
        "💫 оставаться замотивированным\n"
    )