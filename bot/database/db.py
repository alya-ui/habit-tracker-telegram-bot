import datetime
import aiosqlite

DB_PATH = "habits.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            target_days INTEGER,
            reminder_time TEXT
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS logs (
            habit_id INTEGER,
            date TEXT,
            done INTEGER
        )''')
        await db.commit()

async def add_habit(user_id: int, name: str, target_days: int, reminder_time: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO habits (user_id, name, target_days, reminder_time) VALUES (?, ?, ?, ?)",
            (user_id, name, target_days, reminder_time)
        )
        await db.commit()
        return cur.lastrowid

async def get_habits(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, name, target_days, reminder_time FROM habits WHERE user_id = ?",
            (user_id,)
        )
        return await cur.fetchall()

async def mark_done(habit_id: int, date: str = None):
    if date is None:
        date = datetime.date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM logs WHERE habit_id=? AND date=?", (habit_id, date))
        await db.execute("INSERT INTO logs (habit_id, date, done) VALUES (?, ?, 1)", (habit_id, date))
        await db.commit()

async def is_done_today(habit_id: int):
    today = datetime.date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT done FROM logs WHERE habit_id=? AND date=?", (habit_id, today))
        row = await cur.fetchone()
    return row is not None and row[0] == 1

async def get_streak(habit_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT date FROM logs WHERE habit_id=? AND done=1 ORDER BY date DESC",
            (habit_id,)
        )
        rows = await cur.fetchall()
    streak = 0
    today = datetime.date.today()
    for row in rows:
        d = datetime.date.fromisoformat(row[0])
        if d == today:
            streak += 1
            today -= datetime.timedelta(days=1)
        else:
            break
    return streak

async def get_stats(habit_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT date FROM logs WHERE habit_id=? ORDER BY date ASC LIMIT 1", (habit_id,))
        first = await cur.fetchone()
        if not first:
            return {"done": 0, "total": 0, "percent": 0, "streak": 0}
        start = datetime.date.fromisoformat(first[0])
        today = datetime.date.today()
        total = (today - start).days + 1
        cur = await db.execute("SELECT COUNT(*) FROM logs WHERE habit_id=? AND done=1", (habit_id,))
        done_count = (await cur.fetchone())[0]
    percent = (done_count / total * 100) if total else 0
    streak = await get_streak(habit_id)
    return {"done": done_count, "total": total, "percent": round(percent, 1), "streak": streak}