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
            reminder_time TEXT,
            is_active INTEGER DEFAULT 1,
            completed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            current_streak INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0
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

async def get_users_with_missed_habits():
    
    from datetime import datetime, timedelta
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT id, user_id, name, reminder_time, completed_at, created_at
               FROM habits 
               WHERE is_active = 1 AND reminder_time IS NOT NULL"""
        )
        rows = await cursor.fetchall()
        
        missed_habits = []
        now = datetime.now()
        today = now.date()
        
        for habit_id, user_id, name, reminder_time, completed_at, created_at in rows:
            if not reminder_time:
                continue
            
            reminder_hour, reminder_minute = map(int, reminder_time.split(':'))
            reminder_datetime_today = datetime(
                today.year, today.month, today.day,
                reminder_hour, reminder_minute
            )
            
            if now > reminder_datetime_today:
                if completed_at:
                    # Преобразуем completed_at в datetime
                    if isinstance(completed_at, str):
                        completed_date = datetime.strptime(completed_at, '%Y-%m-%d').date()
                    else:
                        completed_date = completed_at
                    
                    if completed_date < today:
                        days_missed = (today - completed_date).days
                        if days_missed >= 1:
                            missed_habits.append({
                                "user_id": user_id,
                                "habit_id": habit_id,
                                "habit_name": name,
                                "days_missed": days_missed,
                                "reminder_time": reminder_time
                            })
                else:
                    if created_at:
                        if isinstance(created_at, str):
                            created_date = datetime.strptime(created_at.split(' ')[0], '%Y-%m-%d').date()
                        else:
                            created_date = created_at
                        days_missed = (today - created_date).days
                    else:
                        days_missed = 1
                    
                    missed_habits.append({
                        "user_id": user_id,
                        "habit_id": habit_id,
                        "habit_name": name,
                        "days_missed": days_missed,
                        "reminder_time": reminder_time
                    })
        
        return missed_habits

async def get_target_days(habit_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT target_days FROM habits WHERE id = ?', (habit_id,))
        result = await cursor.fetchone()
        return result[0] if result else 0


async def get_days_since_creation(habit_id: int) -> int:
    from datetime import date
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT created_at FROM habits WHERE id = ?', (habit_id,))
        result = await cursor.fetchone()
        if result and result[0]:
            created_str = result[0].split(' ')[0]
            created = date.fromisoformat(created_str)
            return (date.today() - created).days
        return 0