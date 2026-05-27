# habit-tracker-telegram-bot
Асинхронный тг бот для отслеживания привычек, напоминаний и мотивации 

Бот помогает пользователю:
- создавать новые привычки;
- указывать количество дней для выполнения привычки;
- задавать время напоминания;
- просматривать список своих привычек;
- отмечать привычку как выполненную;
- смотреть статистику и прогресс;
- получать мотивационные сообщения;
- не забывать о привычках благодаря напоминаниям.
  
Участники: 
- Федоровых Алина Алексеевна  253;
- Кулагина Дарья Евгеньевна 253;
- Мосина Наталья  Александровна 253;
- Александрова Ольга Алексеевна 253.

Основной функционал:
Бот умеет...
- ...запускаться по команде `/start`;
- ...показывать главное меню;
- ...добавлять привычку через кнопку или команду `/add_habit`;
- ...сохранять привычки в базу данных;
- ...показывать список привычек пользователя;
- ...выводить отдельную карточку привычки с кнопками;
- ...отмечать привычку как выполненную;
- ...считать текущую серию выполнений;
- ...показывать статистику по привычкам;
- ...показывать справку через кнопку «Помощь»;
- ...отправлять напоминания;
- ...выводить мотивационные сообщения за серии выполнений.

## Структура репозитория
```
.idea/
├── inspectionProfiles/
│ └── profile_settings.xml
├── .gitignore
├── misc.xml
├── modules.xml
├── tg bot.iml
└── vcs.xml

bot/
├── database/
│ ├── init.py
│ └── db.py
├── handlers/
│ ├── init.py
│ ├── habits.py
│ └── start.py
├── keyboards/
│ ├── init.py
│ └── inline.py
├── services/
│ ├── init.py
│ ├── missed_checker.py
│ └── remis.py
├── texts/
│ ├── init.py
│ ├── messages.py
│ └── missed_messages.py
├── init.py
├── config.py
├── habits.db
└── main.py

.env.save
.gitignore
README.md
requirements.txt
```

## Как запустить проект

### Windows
```bash
git clone https://github.com/alya-ui/habit-tracker-telegram-bot.git
cd habit-tracker-telegram-bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.save .env
# (Откройте .env и вставьте токен: BOT_TOKEN=ваш_токен_бота)
python -m bot.main

### Linux/ macOS
```bash

git clone https://github.com/alya-ui/habit-tracker-telegram-bot.git
cd habit-tracker-telegram-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.save .env
# (Откройте .env и вставьте токен: BOT_TOKEN=ваш_токен_бота)
python -m bot.main
