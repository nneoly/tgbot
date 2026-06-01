import telebot
from telebot import types
import json
import os
from datetime import datetime, timedelta
import threading
import time as time_module
import random

TOKEN = '8691065371:AAGzNdw9fJWSID6WzTIBtBsbV5V-xoT_C8c'
bot = telebot.TeleBot(TOKEN)

DATA_FILE = 'habits_data.json'
GAME_STATS_FILE = 'game_stats.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_game_stats():
    if os.path.exists(GAME_STATS_FILE):
        with open(GAME_STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_game_stats(stats):
    with open(GAME_STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def today_str():
    return datetime.now().strftime('%Y-%m-%d')

def add_habit(user_id, habit_name):
    data = load_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {}
    
    if habit_name not in data[user_id]:
        data[user_id][habit_name] = {
            'streak': 0,
            'history': {}
        }
        save_data(data)
        return True
    return False

def rename_habit(user_id, old_name, new_name):
    data = load_data()
    user_id = str(user_id)
    
    if user_id in data and old_name in data[user_id]:
        if new_name in data[user_id]:
            return False  
        data[user_id][new_name] = data[user_id].pop(old_name)
        save_data(data)
        return True
    return False

def delete_habit(user_id, habit_name):
    data = load_data()
    user_id = str(user_id)
    
    if user_id in data and habit_name in data[user_id]:
        del data[user_id][habit_name]
        save_data(data)
        return True
    return False

def mark_habit(user_id, habit_name):
    data = load_data()
    user_id = str(user_id)
    today = today_str()
    
    if user_id in data and habit_name in data[user_id]:
        if data[user_id][habit_name]['history'].get(today):
            return False
        
        data[user_id][habit_name]['history'][today] = True
        streak = data[user_id][habit_name].get('streak', 0)
        data[user_id][habit_name]['streak'] = streak + 1
        save_data(data)
        return True
    return False

def get_stats(user_id, habit_name):
    data = load_data()
    user_id = str(user_id)
    
    if user_id not in data or habit_name not in data[user_id]:
        return None
    
    habit = data[user_id][habit_name]
    streak = habit['streak']
    history = habit['history']
    
    week_stats = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        completed = history.get(date, False)
        week_stats.append((date, completed))
    
    completed_count = sum(1 for _, c in week_stats if c)
    percent = (completed_count / 7) * 100
    
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    graph = ""
    for i, (_, completed) in enumerate(reversed(week_stats)):
        symbol = "✅" if completed else "⬜"
        graph += f"{days[i]}: {symbol}  "
    
    return f"📈 **{habit_name}**\n🔥 Серия: {streak} дней\n📅 Выполнение за неделю: {percent:.0f}%\n\n{graph}"

def get_all_stats_text(user_id):
    data = load_data()
    user_id = str(user_id)
    
    if user_id not in data or not data[user_id]:
        return "📋 У тебя пока нет привычек. Добавь первую!"
    
    result = "📊 **Твои привычки:**\n\n"
    for habit_name in data[user_id].keys():
        habit = data[user_id][habit_name]
        streak = habit['streak']
        today_done = habit['history'].get(today_str(), False)
        status = "✅" if today_done else "⏳"
        result += f"{status} **{habit_name}** — серия: {streak} дней\n"
    
    return result

def get_winner(player_choice, bot_choice):
    if player_choice == bot_choice:
        return "draw"
    if (player_choice == "камень" and bot_choice == "ножницы") or \
       (player_choice == "ножницы" and bot_choice == "бумага") or \
       (player_choice == "бумага" and bot_choice == "камень"):
        return "win"
    return "lose"

def update_game_stats(user_id, result):
    stats = load_game_stats()
    user_id = str(user_id)
    if user_id not in stats:
        stats[user_id] = {'wins': 0, 'losses': 0, 'draws': 0}
    
    if result == "win":
        stats[user_id]['wins'] += 1
    elif result == "lose":
        stats[user_id]['losses'] += 1
    else:
        stats[user_id]['draws'] += 1
    save_game_stats(stats)

def get_game_stats_text(user_id):
    stats = load_game_stats()
    user_id = str(user_id)
    
    if user_id not in stats:
        return "🎮 У тебя пока нет сыгранных игр!"
    
    s = stats[user_id]
    total = s['wins'] + s['losses'] + s['draws']
    winrate = (s['wins'] / total * 100) if total > 0 else 0
    
    return f"🎮 **Твоя статистика игр:**\n\n✅ Побед: {s['wins']}\n❌ Поражений: {s['losses']}\n🤝 Ничьих: {s['draws']}\n📊 Всего: {total}\n🏆 Винрейт: {winrate:.1f}%"

def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_add = types.KeyboardButton('➕ Добавить привычку')
    btn_list = types.KeyboardButton('📋 Мои привычки')
    btn_today = types.KeyboardButton('✅ Отметить выполнение')
    btn_stats = types.KeyboardButton('📊 Статистика привычек')
    btn_edit = types.KeyboardButton('✏️ Изменить привычку')
    btn_delete = types.KeyboardButton('🗑️ Удалить привычку')
    btn_game = types.KeyboardButton('🎮 Камень-ножницы-бумага')
    btn_game_stats = types.KeyboardButton('🏆 Статистика игр')
    keyboard.add(btn_add, btn_list, btn_today, btn_stats, btn_edit, btn_delete, btn_game, btn_game_stats)
    return keyboard

def get_game_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    btn_rock = types.InlineKeyboardButton('✊ Камень', callback_data='game_rock')
    btn_paper = types.InlineKeyboardButton('✋ Бумага', callback_data='game_paper')
    btn_scissors = types.InlineKeyboardButton('✌️ Ножницы', callback_data='game_scissors')
    keyboard.add(btn_rock, btn_paper, btn_scissors)
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "📌 **Трекер привычек**\n\n"
        "Бот для отслеживания привычек! Вот что я умею:\n\n"
        "• Добавить любые привычки\n"
        "• Отметить выполнение каждый день\n"
        "• Следить за прогрессом\n\n"
        "• Играй с ботом в камень-ножницы-бумага\n"
        "⏰ Каждый вечер в 21:00 я напомню отметить привычки!"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == '➕ Добавить привычку')
def ask_for_habit(message):
    msg = bot.send_message(message.chat.id, "📝 Напиши название привычки.")
    bot.register_next_step_handler(msg, save_habit)

def save_habit(message):
    habit_name = message.text.strip().lower()
    
    if not habit_name:
        bot.send_message(message.chat.id, "❌ Название не может быть пустым!")
        return
    
    if add_habit(message.chat.id, habit_name):
        bot.send_message(message.chat.id, f"✅ Привычка **{habit_name}** добавлена!", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, f"⚠️ Привычка **{habit_name}** уже существует!", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '✏️ Изменить привычку')
def ask_for_rename(message):
    data = load_data()
    user_id = str(message.chat.id)
    
    if user_id not in data or not data[user_id]:
        bot.send_message(message.chat.id, "📋 У тебя пока нет привычек для изменения!")
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for habit in data[user_id].keys():
        keyboard.add(types.InlineKeyboardButton(text=habit, callback_data=f"rename_{habit}"))
    
    bot.send_message(message.chat.id, "✏️ Какую привычку хочешь переименовать?", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith('rename_'))
def ask_for_new_name(call):
    old_name = call.data[7:]
    msg = bot.send_message(call.message.chat.id, f"📝 Введи новое название для привычки **{old_name}**:", parse_mode='Markdown')
    bot.register_next_step_handler(msg, lambda m: save_rename(m, old_name))

def save_rename(message, old_name):
    new_name = message.text.strip().lower()
    
    if not new_name:
        bot.send_message(message.chat.id, "❌ Название не может быть пустым!")
        return
    
    if rename_habit(message.chat.id, old_name, new_name):
        bot.send_message(message.chat.id, f"✅ Привычка **{old_name}** переименована в **{new_name}**!", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, f"⚠️ Не удалось переименовать. Возможно, привычка **{new_name}** уже существует!", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '🗑️ Удалить привычку')
def ask_for_delete(message):
    data = load_data()
    user_id = str(message.chat.id)
    
    if user_id not in data or not data[user_id]:
        bot.send_message(message.chat.id, "📋 У тебя пока нет привычек для удаления!")
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for habit in data[user_id].keys():
        keyboard.add(types.InlineKeyboardButton(text=habit, callback_data=f"delete_{habit}"))
    
    bot.send_message(message.chat.id, "🗑️ Какую привычку хочешь удалить?", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith('delete_'))
def confirm_delete(call):
    habit_name = call.data[7:]
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn_yes = types.InlineKeyboardButton('✅ Да, удалить', callback_data=f"confirm_yes_{habit_name}")
    btn_no = types.InlineKeyboardButton('❌ Нет, отмена', callback_data="confirm_no")
    keyboard.add(btn_yes, btn_no)
    
    bot.send_message(call.message.chat.id, f"⚠️ Ты уверен, что хочешь удалить привычку **{habit_name}**? Вся статистика пропадёт!", parse_mode='Markdown', reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith('confirm_yes_'))
def execute_delete(call):
    habit_name = call.data[12:]
    
    if delete_habit(call.message.chat.id, habit_name):
        bot.send_message(call.message.chat.id, f"🗑️ Привычка **{habit_name}** удалена!", parse_mode='Markdown')
    else:
        bot.send_message(call.message.chat.id, "❌ Не удалось удалить привычку.")

@bot.callback_query_handler(func=lambda call: call.data == 'confirm_no')
def cancel_delete(call):
    bot.send_message(call.message.chat.id, "✅ Удаление отменено.")

@bot.message_handler(func=lambda message: message.text == '📋 Мои привычки')
def list_habits(message):
    text = get_all_stats_text(message.chat.id)
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '✅ Отметить выполнение')
def ask_for_mark(message):
    data = load_data()
    user_id = str(message.chat.id)
    
    if user_id in data and data[user_id]:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for habit in data[user_id].keys():
            keyboard.add(types.KeyboardButton(f"✅ {habit}"))
        keyboard.add(types.KeyboardButton('🔙 Назад'))
        bot.send_message(message.chat.id, "Выбери привычку, которую выполнил сегодня:", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "📋 У тебя пока нет привычек. Нажми «Добавить привычку»!")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('✅ '))
def mark_habit_callback(message):
    habit_name = message.text[2:].strip()
    
    if mark_habit(message.chat.id, habit_name):
        bot.send_message(message.chat.id, f"✅ Отметил(а) **{habit_name}** на сегодня! 🔥", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, f"⚠️ **{habit_name}** уже отмечен(а) сегодня или не существует!", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '📊 Статистика привычек')
def ask_for_stats(message):
    data = load_data()
    user_id = str(message.chat.id)
    
    if user_id in data and data[user_id]:
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        for habit in data[user_id].keys():
            keyboard.add(types.InlineKeyboardButton(text=habit, callback_data=f"stats_{habit}"))
        bot.send_message(message.chat.id, "📊 По какой привычке показать детальную статистику?", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "📋 У тебя пока нет привычек. Добавь первую!")

@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith('stats_'))
def show_stats(call):
    habit_name = call.data[6:]
    stats = get_stats(call.message.chat.id, habit_name)
    if stats:
        bot.send_message(call.message.chat.id, stats, parse_mode='Markdown')
    else:
        bot.send_message(call.message.chat.id, "❌ Не удалось получить статистику.")

@bot.message_handler(func=lambda message: message.text == '🎮 Камень-ножницы-бумага')
def game_menu(message):
    bot.send_message(message.chat.id, "✊✋✌️ Выбери свой ход:", reply_markup=get_game_keyboard())

@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith('game_'))
def game_move(call):
    choice_map = {
        'game_rock': 'камень',
        'game_paper': 'бумага',
        'game_scissors': 'ножницы'
    }
    player_choice = choice_map.get(call.data)
    if not player_choice:
        return
    
    bot_choice = random.choice(['камень', 'ножницы', 'бумага'])
    result = get_winner(player_choice, bot_choice)
    
    emoji_map = {'камень': '✊', 'ножницы': '✌️', 'бумага': '✋'}
    
    if result == "win":
        result_text = "🎉 Ты выиграл!"
        update_game_stats(call.message.chat.id, "win")
    elif result == "lose":
        result_text = "😭 Ты проиграл!"
        update_game_stats(call.message.chat.id, "lose")
    else:
        result_text = "🤝 Ничья!"
        update_game_stats(call.message.chat.id, "draw")
    
    bot.send_message(
        call.message.chat.id,
        f"📊 **Результат:**\n\n"
        f"Твой ход: {emoji_map[player_choice]} {player_choice}\n"
        f"Мой ход: {emoji_map[bot_choice]} {bot_choice}\n\n"
        f"{result_text}",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == '🏆 Статистика игр')
def show_game_stats(message):
    stats_text = get_game_stats_text(message.chat.id)
    bot.send_message(message.chat.id, stats_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == '🔙 Назад')
def back_to_main(message):
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=get_main_keyboard())

def daily_check():
    while True:
        now = datetime.now()
        target_time = now.replace(hour=21, minute=0, second=0, microsecond=0)
        if now >= target_time:
            target_time += timedelta(days=1)
        
        seconds_to_wait = (target_time - now).total_seconds()
        time_module.sleep(seconds_to_wait)
        
        data = load_data()
        today = today_str()
        
        for user_id, habits in data.items():
            unchecked = []
            for habit_name, habit_data in habits.items():
                if not habit_data['history'].get(today):
                    unchecked.append(habit_name)
            
            if unchecked:
                habits_list = "\n".join([f"• {h}" for h in unchecked])
                bot.send_message(
                    int(user_id),
                    f"⏰ **Напоминание!**\nТы ещё не отметил(а) сегодня:\n{habits_list}\n\nНажми «Отметить выполнение» в меню!",
                    parse_mode='Markdown'
                )

def start_scheduler():
    thread = threading.Thread(target=daily_check, daemon=True)
    thread.start()

@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    bot.send_message(
        message.chat.id,
        "❓ Неизвестная команда. Используй кнопки меню 👇",
        reply_markup=get_main_keyboard()
    )

if __name__ == '__main__':
    print("Бот запущен")
    start_scheduler()
    bot.polling(none_stop=True, interval=0)