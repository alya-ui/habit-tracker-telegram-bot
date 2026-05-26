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
    await add_created_at_column()
async def get_target_days(habit_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT target_days FROM habits WHERE id = ?", (habit_id,))
        row = await cur.fetchone()
        return row[0] if row else 0

async def add_habit(user_id: int, name: str, target_days: int, reminder_time: str):
    user_id = int(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO habits (user_id, name, target_days, reminder_time) VALUES (?, ?, ?, ?)",
            (user_id, name, target_days, reminder_time)
        )
        await db.commit()
        return cur.lastrowid

async def get_habits(user_id: int):
    user_id = int(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, name, target_days, reminder_time FROM habits WHERE user_id = ?",
            (user_id,)
        )
        rows = await cur.fetchall()
        print(f"DEBUG: get_habits для user_id {user_id} нашла {len(rows)} привычек")
        return rows

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
async def get_days_since_creation(habit_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT created_at FROM habits WHERE id = ?", (habit_id,))
        row = await cur.fetchone()
        if not row:
            return 0
        created = datetime.datetime.fromisoformat(row[0]).date()
        today = datetime.date.today()
        return (today - created).days
async def add_created_at_column():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("PRAGMA table_info(habits)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        if 'created_at' not in column_names:
            await db.execute("ALTER TABLE habits ADD COLUMN created_at TIMESTAMP")
            await db.execute("UPDATE habits SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
            await db.commit()
            print("✅ Колонка created_at добавлена и заполнена")
async def get_best_streak(habit_id: int) -> int:

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT date FROM logs WHERE habit_id=? AND done=1 ORDER BY date ASC",
            (habit_id,)
        )
        rows = await cur.fetchall()
    if not rows:
        return 0
    best = 0
    current = 1
    prev = datetime.date.fromisoformat(rows[0][0])
    for row in rows[1:]:
        d = datetime.date.fromisoformat(row[0])
        if d == prev + datetime.timedelta(days=1):
            current += 1
        else:
            if current > best:
                best = current
            current = 1
        prev = d
    if current > best:
        best = current
    return best