import asyncio
from aiogram import Bot, Dispatcher
from bot.config import BOT_TOKEN
from bot.handlers import start, habits
from bot.database import db
from bot.services import remis


async def main():
    await db.init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(habits.router)
    asyncio.create_task(remis.reminder_worker(bot))
    asyncio.create_task(remis.missed_check_worker())
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())