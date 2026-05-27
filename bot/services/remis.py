import asyncio
import datetime
import aiosqlite
from aiogram import Bot
from bot.database import db
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def done_keyboard(habit_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Выполнено",
                    callback_data=f"complete_{habit_id}"
                )
            ]
        ]
    )

async def reminder_worker(bot: Bot):
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        async with aiosqlite.connect(db.DB_PATH) as conn:
            cur = await conn.execute("SELECT id, user_id, name FROM habits WHERE reminder_time = ?", (now,))
            rows = await cur.fetchall()
        for hid, uid, name in rows:
            if not await db.is_done_today(hid):
     await bot.send_message(
    uid,
    f"⏰ Напоминание: {name}\nОтметь выполнение:",
    reply_markup=done_keyboard(hid)
)
        await asyncio.sleep(60)

async def missed_check_worker():
    while True:
        now = datetime.datetime.now()
        target = now.replace(hour=0, minute=5, second=0, microsecond=0)
        if now > target:
            target += datetime.timedelta(days=1)
        await asyncio.sleep((target - now).seconds)
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        async with aiosqlite.connect(db.DB_PATH) as conn:
            cur = await conn.execute("SELECT id FROM habits")
            all_habits = await cur.fetchall()
            for (hid,) in all_habits:
                cur2 = await conn.execute("SELECT done FROM logs WHERE habit_id=? AND date=?", (hid, yesterday))
                if await cur2.fetchone() is None:
                    await conn.execute("INSERT INTO logs (habit_id, date, done) VALUES (?,?,0)", (hid, yesterday))
            await conn.commit()
