import datetime
import sqlite3
import threading
import time
import telebot
from telebot import types

BOT_USERNAME = "DZ2623_BOT" 

TOKEN = "8816124858:AAE-Uq47tVIITaNXMcqfIX5H4ZIvQWFua4U"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 0  # Укажи сюда свой Telegram ID, если нужно

CHANNEL_URL = "https://t.me/+PeFmZgwkf_Y0YzFl"

def init_db():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    # Полностью удаляем таблицы при запуске, чтобы структура всегда была актуальной
    cursor.execute('DROP TABLE IF EXISTS tasks')
    cursor.execute('DROP TABLE IF EXISTS subscribers')
    
    cursor.execute('''
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_target TEXT,
            subject_name TEXT,
            title TEXT,
            description TEXT,
            is_important INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE subscribers (
            chat_id INTEGER PRIMARY KEY,
            last_active TIMESTAMP
        )
    ''')
    
    initial_data = [
        # Понедельник
        ("monday", "⚡ Физика", "График СРО (Кинематика, Динамика и Динамика твердого тела)", "Содержание: Поступательное и вращательное движения — основные виды движений. Гравитационные силы. Закон всемирного тяготения. Силы упругости. Закон Гука. Силы трения. Инерциальные системы отсчета. Механический принцип относительности. Сдавать в отдельной тетради в каб. 407 (стол Галии Исатаевны)", 1),
        ("monday", "⚡ Физика", "Задачи из учебника Волькенштейна", "Выполнить номера: № 1.52, 1.53, 1.55, 1.57, 1.58, 1.59, 1.60, 1.61, 1.62, 1.63 (до 15:00)", 1),
        
        # Вторник
        ("tuesday", "🔢 Дискретная математика", "Задание № 144", "Выполнить номера 144 (а, б, в)", 1),
        
        # Среда
        ("wednesday", "💻 ООП", "4 лабораторные работы по ООП Практике", "Выполнить лабораторные: №1, №2, №3, №4", 1),
        
        # Пятница
        ("friday", "🤖 Искусственный Интеллект", "Лабораторные работы №1–№6 (Семинар)", "Выполнить лабораторные работы с №1 по №6 по Системному искусственному интеллекту", 1),
        
        # Воскресенье / До конца недели
        ("sunday", "📖 Философия", "Доклад: Иммануил Кант", "Тема «Немецкая классическая философия / Иммануил Кант»", 0),
        ("sunday", "📖 Философия", "СРО (Эссе): Культ знания в Казахстане", "Объём 250-300 слов. Тема: «Культ знания в современном Казахстане» (до 18 октября)", 1),
        ("sunday", "🏛️ История Казахстана", "6 презентаций к рубежке", "Подготовить 6 презентаций к первой рубежке. Почты для отправки: seitov_erik@mail.ru | seitov43@gmail.com", 1),
        
        # Ближайшие дни / Рекомендации
        ("soon", "🔢 Дискретная математика", "Записать лекции", "Записать прошедшие лекции (кто еще не записал)", 0),
        ("soon", "💻 ООП", "Записать лекции по ООП", "Записать все прошедшие лекции по ООП (рекомендация)", 0)
    ]
    
    cursor.executemany("INSERT INTO tasks (day_target, subject_name, title, description, is_important) VALUES (?, ?, ?, ?, ?)", initial_data)
    conn.commit()
    conn.close()

init_db()

def update_activity(chat_id):
    """Обновляет время последней активности пользователя в базе"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    now = datetime.datetime.now()
    cursor.execute('''
        INSERT INTO subscribers (chat_id, last_active) VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET last_active = ?
    ''', (chat_id, now, now))
    conn.commit()
    conn.close()

DAYS_MENU = {
    "day_monday": "🟢 ДЗ на Понедельник",
    "day_tuesday": "🟠 ДЗ на Вторник",
    "day_wednesday": "🟡 ДЗ на Среду",
    "day_friday": "🔵 ДЗ на Пятницу",
    "day_sunday": "🟣 ДЗ на Воскресенье / Конец недели",
    "day_soon": "📌 Задания на ближайшие дни"
}

SCHEDULE = {
    "sched_mon": (
        "🟢 Понедельник (ИС 26-23):\n\n"
        "⏰ 09.00 - 09.50 | Системы искусственного интеллекта (сем)\n   📍 Ауд. 406 | Мысжанов З.М.\n\n"
        "⏰ 10.00 - 11.50 | История Казахстана (2 пары подряд)\n   📍 Ауд. 211 | Сеитов Е.Т.\n\n"
        "⏰ 13.00 - 13.50 | ООП (лекция)\n   📍 Ауд. 211 | ст. преп. Исаева М.А.\n\n"
        "⏰ 14.00 - 14.50 | Физика (сем)\n   📍 Ауд. 120 | Мухамедрахимова Г.И."
    ),
    "sched_tue": (
        "🟢 Вторник (ИС 26-23):\n\n"
        "⏰ 13.00 - 15.50 | Дискретная математика и теория вероятностей (3 пары подряд)\n   📍 Ауд. 212 / 405 | ст.преп. Есентемирова А.К."
    ),
    "sched_wed": (
        "🟢 Среда (ИС 26-23):\n\n"
        "⏰ 15.00 - 15.50 | Дискретная математика и теория вероятностей (сем)\n   📍 Ауд. 304 | ст.преп. Есентемирова А.К.\n\n"
        "⏰ 16.00 - 16.50 | ООП (сем)\n   📍 Ауд. 400 | ст. преп. Исаева М.А.\n\n"
        "⏰ 17.00 - 17.50 | Системы искусственного интеллекта (сем)\n   📍 Ауд. 417 | Мысжанов З.М."
    ),
    "sched_fri": (
        "🟢 Пятница (ИС 26-23):\n\n"
        "⏰ 10.00 - 10.50 | История Казахстана (семинар)\n   📍 Ауд. 415 | Сеитов Э.Т.\n\n"
        "⏰ 11.00 - 11.50 | Философия (сем)\n   📍 Ауд. 311 | преп. Жукенова А.А.\n\n"
        "⏰ 12.00 - 12.50 | Физика (сем)\n   📍 Ауд. 426 | доц. Мухамедрахимова Г.И.\n\n"
        "⏰ 13.00 - 13.50 | Системы искусственного интеллекта (лекция)\n   📍 Ауд. 212 | ст.преп. Абдрахманова А.З.\n\n"
        "⏰ 14.00 - 14.50 | Физика (лекция)\n   📍 Ауд. 211 | доц. Мухамедрахимова Г.И."
    )
}

def get_current_status():
    now = datetime.datetime.now()
    weekday = now.weekday()
    current_time = now.time()
    
    if weekday == 0:
        if datetime.time(9, 0) <= current_time <= datetime.time(9, 50):
            return "🔥 Сейчас идет: Системы ИИ (ауд. 406)"
        elif datetime.time(10, 0) <= current_time <= datetime.time(11, 50):
            return "🔥 Сейчас идет: История Казахстана (ауд. 211)"
        elif datetime.time(11, 50) < current_time < datetime.time(13, 0):
            return "☕ Большая перемена / Обед"
        elif datetime.time(13, 0) <= current_time <= datetime.time(13, 50):
            return "🔥 Сейчас идет: ООП (ауд. 211)"
        elif datetime.time(14, 0) <= current_time <= datetime.time(14, 50):
            return "🔥 Сейчас идет: Физика (ауд. 120)"
            
    elif weekday == 1:
        if datetime.time(13, 0) <= current_time <= datetime.time(15, 50):
            return "🔥 Сейчас идет: Дискретная математика (ауд. 212/405)"
            
    elif weekday == 2:
        if datetime.time(15, 0) <= current_time <= datetime.time(15, 50):
            return "🔥 Сейчас идет: Дискретная математика (ауд. 304)"
        elif datetime.time(16, 0) <= current_time <= datetime.time(16, 50):
            return "🔥 Сейчас идет: ООП (ауд. 400)"
        elif datetime.time(17, 0) <= current_time <= datetime.time(17, 50):
            return "🔥 Сейчас идет: Системы ИИ (ауд. 417)"
            
    elif weekday == 4:
        if datetime.time(10, 0) <= current_time <= datetime.time(10, 50):
            return "🔥 Сейчас идет: История Казахстана (ауд. 415)"
        elif datetime.time(11, 0) <= current_time <= datetime.time(11, 50):
            return "🔥 Сейчас идет: Философия (ауд. 311)"
        elif datetime.time(12, 0) <= current_time <= datetime.time(12, 50):
            return "🔥 Сейчас идет: Физика (ауд. 426)"
        elif datetime.time(13, 0) <= current_time <= datetime.time(13, 50):
            return "🔥 Сейчас идет: Системы ИИ (ауд. 212)"
        elif datetime.time(14, 0) <= current_time <= datetime.time(14, 50):
            return "🔥 Сейчас идет: Физика (ауд. 211)"

    if weekday in [5, 6]:
        return "🌴 Сегодня выходной, пар нет!"
    return "🌴 Сейчас пар нет / Перерыв"

def daily_scheduler():
    already_sent = False
    while True:
        now = datetime.datetime.now()
        if now.hour == 8 and now.minute == 0 and not already_sent:
            weekday_keys = {0: "sched_mon", 1: "sched_tue", 2: "sched_wed", 4: "sched_fri"}
            day_text = SCHEDULE.get(weekday_keys.get(now.weekday()), "🌴 Сегодня по расписанию пар нет! Отдыхаем.")
            
            msg = f"🌅 Доброе утро, ИС 26-23!\n\n📅 Сегодняшнее расписание:\n\n{day_text}\n\nУдачной учебы! 🚀"
            
            conn = sqlite3.connect('tasks.db')
            cursor = conn.cursor()
            cursor.execute("SELECT chat_id FROM subscribers")
            chats = cursor.fetchall()
            conn.close()
            
            for (cid,) in chats:
                try:
                    bot.send_message(cid, msg)
                except Exception as e:
                    print(f"Ошибка рассылки: {e}")
                    
            already_sent = True
        
        if now.minute != 0:
            already_sent = False
            
        time.sleep(30)

threading.Thread(target=daily_scheduler, daemon=True).start()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    update_activity(message.chat.id)
    status_text = get_current_status()
    
    if message.chat.type in ['group', 'supergroup']:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🔓 Открыть трекер индивидуально (в ЛС)", url=f"https://t.me/{BOT_USERNAME}?start=true"))
        markup.add(types.InlineKeyboardButton("📚 Канал с лекциями и материалами", url=CHANNEL_URL))
        
        group_msg = f"👋 Трекер группы ИС 26-23\n\n📌 Статус: {status_text}\n\nЧтобы посмотреть задачи и расписание конфиденциально, перейдите в личный чат с ботом:"
        bot.send_message(message.chat.id, group_msg, reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        for key, name in DAYS_MENU.items():
            markup.add(types.InlineKeyboardButton(name, callback_data=key))
        markup.add(types.InlineKeyboardButton("📅 Расписание пар (ИС 26-23)", callback_data="menu_schedule"))
        markup.add(types.InlineKeyboardButton("📚 Канал с лекциями и материалами", url=CHANNEL_URL))
        
        welcome_msg = f"👋 Привет! Это твой личный кабинет трекера ИС 26-23.\n\n📌 Статус: {status_text}\n\nВыбери, на какой день посмотреть домашнее задание:"
        bot.send_message(message.chat.id, welcome_msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    update_activity(call.message.chat.id)
    
    if call.data in DAYS_MENU.keys():
        bot.answer_callback_query(call.id)
        day_key = call.data.replace("day_", "")
        day_title = DAYS_MENU[call.data]
        
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, subject_name, title, description, is_important FROM tasks WHERE day_target = ?", (day_key,))
        rows = cursor.fetchall()
        conn.close()
        
        text = f"📋 {day_title}\n\n"
        if not rows:
            text += "📭 На этот день заданий нет."
        else:
            for i, row in enumerate(rows, 1):
                task_id, subj_name, title, desc, is_imp = row
                icon = "🔴" if is_imp else "📌"
                text += f"{i}. {icon} {subj_name} — {title}\n"
                text += f"   └ {desc}\n"
                text += f"   🆔 ID: {task_id}\n\n"
                
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 Главное меню", callback_data="back_to_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "menu_schedule":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("Понедельник", callback_data="sched_mon"),
            types.InlineKeyboardButton("Вторник", callback_data="sched_tue"),
            types.InlineKeyboardButton("Среда", callback_data="sched_wed"),
            types.InlineKeyboardButton("Пятница", callback_data="sched_fri")
        )
        markup.add(types.InlineKeyboardButton("🔄 Главное меню", callback_data="back_to_menu"))
        bot.edit_message_text("📅 Выберите день недели:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data in SCHEDULE.keys():
        bot.answer_callback_query(call.id)
        text = SCHEDULE[call.data]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📅 К дням недели", callback_data="menu_schedule"))
        markup.add(types.InlineKeyboardButton("🔄 Главное меню", callback_data="back_to_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "back_to_menu":
        bot.answer_callback_query(call.id)
        status_text = get_current_status()
        markup = types.InlineKeyboardMarkup(row_width=1)
        for key, name in DAYS_MENU.items():
            markup.add(types.InlineKeyboardButton(name, callback_data=key))
        markup.add(types.InlineKeyboardButton("📅 Расписание пар (ИС 26-23)", callback_data="menu_schedule"))
        markup.add(types.InlineKeyboardButton("📚 Канал с лекциями и материалами", url=CHANNEL_URL))
        
        menu_msg = f"📚 Личный кабинет ИС 26-23\n\n📌 Статус: {status_text}\n\nВыбери, на какой день посмотреть домашнее задание:"
        bot.edit_message_text(menu_msg, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "admin_add":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "✍️ Пришли новую задачу одной строчкой через `|`:\n\n"
            "`день | Название предмета | Название | Описание | 1_или_0`\n\n"
            "Доступные дни:\n"
            "• `monday` (Понедельник)\n"
            "• `tuesday` (Вторник)\n"
            "• `wednesday` (Среда)\n"
            "• `friday` (Пятница)\n"
            "• `sunday` (Воскресенье)\n"
            "• `soon` (Ближайшие дни)"
        )
        bot.register_next_step_handler(msg, process_add_task)

    elif call.data == "admin_del":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "🗑️ Напиши ID задачи для удаления:")
        bot.register_next_step_handler(msg, process_del_task)

    elif call.data == "admin_stats":
        bot.answer_callback_query(call.id)
        show_stats_logic(call.message.chat.id)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    update_activity(message.chat.id)
    if ADMIN_ID != 0 and message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, f"❌ Отказано в доступе. Твой ID: `{message.from_user.id}`", parse_mode="Markdown")
        return
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ Добавить задание", callback_data="admin_add"),
        types.InlineKeyboardButton("🗑️ Удалить задание", callback_data="admin_del"),
        types.InlineKeyboardButton("📊 Статистика активности", callback_data="admin_stats")
    )
    
    bot.send_message(message.chat.id, "👑 Панель старосты\nЧто хочешь сделать?", reply_markup=markup)

@bot.message_handler(commands=['stats'])
def stats_command(message):
    update_activity(message.chat.id)
    if ADMIN_ID != 0 and message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Доступно только администратору.")
        return
    show_stats_logic(message.chat.id)

def show_stats_logic(chat_id):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    now = datetime.datetime.now()
    day_ago = now - datetime.timedelta(days=1)
    week_ago = now - datetime.timedelta(days=7)
    month_ago = now - datetime.timedelta(days=30)
    
    cursor.execute("SELECT COUNT(*) FROM subscribers")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM subscribers WHERE last_active >= ?", (day_ago,))
    active_day = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM subscribers WHERE last_active >= ?", (week_ago,))
    active_week = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM subscribers WHERE last_active >= ?", (month_ago,))
    active_month = cursor.fetchone()[0]
    
    conn.close()

    text = (
        f"📊 *Аналитика активности бота ИС 26-23*\n\n"
        f"👥 Всего пользователей: *{total}*\n"
        f"🔥 Активных за 24 часа: *{active_day}*\n"
        f"📈 Активных за неделю: *{active_week}*\n"
        f"📅 Активных за месяц: *{active_month}*"
    )
    bot.send_message(chat_id, text, parse_mode="Markdown")

def process_add_task(message):
    try:
        parts = [p.strip() for p in message.text.split('|')]
        if len(parts) != 5:
            bot.send_message(message.chat.id, "❌ Неверный формат. Используй ровно 4 разделителя `|`.")
            return
        
        day_target, subj_name, title, desc, is_imp = parts
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (day_target, subject_name, title, description, is_important) VALUES (?, ?, ?, ?, ?)",
                       (day_target, subj_name, title, desc, int(is_imp)))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Задача успешно добавлена в базу!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

def process_del_task(message):
    try:
        task_id = int(message.text.strip())
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Задача с ID {task_id} удалена!")
    except Exception:
        bot.send_message(message.chat.id, "❌ Неверный ID.")

print("🤖 Бот запущен! Все исправления и статистика внедрены.")
bot.polling(none_stop=True)