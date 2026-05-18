import asyncio
from aiogram import Bot, Dispatcher
from bot.config import BOT_TOKEN
from bot.handlers import start, habits


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(habits.router)
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())