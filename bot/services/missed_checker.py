import asyncio
from datetime import datetime
from aiogram import Bot
from bot.database.db import get_users_with_missed_habits
from bot.texts.missed_messages import get_missed_message

async def check_missed_days(bot: Bot):
    last_sent = {}
    
    while True:
        try:
            now = datetime.now()
            missed_habits = await get_users_with_missed_habits()
            
            for habit in missed_habits:
                user_id = habit["user_id"]
                habit_id = habit["habit_id"]
                days_missed = habit["days_missed"]
                key = f"{user_id}_{habit_id}"
                
                send_days = [1, 3, 5, 7, 10, 14]
                should_send = days_missed in send_days or (days_missed > 14 and days_missed % 14 == 0)
                
                if should_send and last_sent.get(key) != days_missed:
                    message_text = get_missed_message(days_missed)
                    
                    if message_text:
                        full_message = (
                            f"📊 *Напоминание о привычке*\n\n"
                            f"Ты не отмечал *{habit['habit_name']}* уже *{days_missed}* "
                            f"{'день' if days_missed == 1 else 'дней'}.\n\n"
                            f"{message_text}\n\n"
                            f"🍀 /my_habits - посмотреть привычки\n"
                            f"➕ /add_habit - добавить новую"
                        )
                        
                        try:
                            await bot.send_message(user_id, full_message, parse_mode="Markdown")
                            last_sent[key] = days_missed
                            print(f"📢 Отправлено напоминание о пропуске: {habit['habit_name']} ({days_missed} дн.)")
                        except Exception as e:
                            print(f"❌ Ошибка отправки пользователю {user_id}: {e}")
            
            await asyncio.sleep(3600) 
            
        except Exception as e:
            print(f"❌ Ошибка в check_missed_days: {e}")
            await asyncio.sleep(60)
