import telebot
from telebot import types
import psycopg2
import bcrypt
import os
import re

db_params = {
    'dbname': 'your data',
    'user': 'your data',
    'password': 'your data',
    'host': 'your data',
    'port': 'your data'
}

conn = psycopg2.connect(**db_params)
cursor = conn.cursor()

API = 'Your Token'
bot = telebot.TeleBot(API) 
admin_chat_ids = #[ADMINS ID!]
bad_words = ["Предупреждение! Дальше будет список слов из ненормативной лексики⏩                                                                                                                                                              ","niga", "nigga", "nigger", "n1ga", "n1gga", "n1gger", "nig@", "nigg@", "n1g@", "n1gg@", 'нига', 'нигга', "нигер", "ниггер", "dick", "pussy", "член", "пизда", "блять", "сука", "пидор", "pidor", "blyat", "suka", "лох", "loh", "чмо", "4мо", "chmo", "4mo"]
ALLOWED_DOMAINS = ["@gmail.com", "@yandex.ru", "@mail.ru", "@inbox.ru", "@bk.ru", "@hotmail.com", "@live.com", "@xakep.ru", "@furmail.ru"]

def verify_password(stored_password, provided_password):
    if isinstance(stored_password, memoryview):
        stored_password = bytes(stored_password)
    return bcrypt.checkpw(provided_password.encode(), stored_password)

def contains_emoji(s):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  
        u"\U0001F300-\U0001F5FF" 
        u"\U0001F680-\U0001F6FF"  
        u"\U0001F1E0-\U0001F1FF"  
        u"\U00002702-\U000027B0"  
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return bool(emoji_pattern.search(s))

# Проверка пароля
def validate_password(password):
    if len(password) < 8 or len(password) > 16:
        return False, "Пароль должен содержать не менее 8 символов и не превышать 16 символов."
    if not re.search(r'[A-Za-zА-Яа-я]', password) or not re.search(r'[0-9]', password):
        return False, "Пароль должен содержать хотя бы одну букву и одну цифру."
    if " " in password:
        return False, "Пароль не должен содержать пробелы."
    if contains_emoji(password):
        return False, "Пароль не может содержать эмодзи."
    for word in bad_words:
        if word in password.lower():
            return False, "Пароль содержит запрещенные слова."
    return True, None

# Установка пароля
def set_user_password(user_id, password, message):
    if message.content_type != 'text':
        bot.send_message(
            message.chat.id,
            "Пароль должен быть текстовым сообщением. Пожалуйста, введите пароль снова:"
        )
        bot.register_next_step_handler(message, lambda msg: set_user_password(user_id, msg.text, msg))
        return
    
    is_valid, validation_message = validate_password(password)
    if not is_valid:
        bot.send_message(
            message.chat.id,
            f"{validation_message} Пожалуйста, введите пароль снова:"
        )
        bot.register_next_step_handler(message, lambda msg: set_user_password(user_id, msg.text, msg))
    else:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)

        try:
            with psycopg2.connect(**db_params) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE users SET password = %s WHERE user_id = %s",
                        (hashed_password, user_id)
                    )
                    conn.commit()
            send_registration_success(message, user_id)
        except Exception as e:
            bot.send_message(message.chat.id, "Ошибка при сохранении пароля. Попробуйте снова.")
            print(f"Ошибка при обновлении пароля: {e}")

def get_all_users():
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id, username FROM users") 
            users = cursor.fetchall()  
            return [{"user_id": user[0], "username": user[1]} for user in users]


def get_user_password(user_id):
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT password FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None

def register_user(user_id, username):
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (user_id, username)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO NOTHING;
            """, (user_id, username))
            conn.commit()

def is_user_registered(user_id):
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = %s;", (user_id,))
            return cursor.fetchone()[0] > 0
        
def email_exists(email):
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s;", (email,))
            return cursor.fetchone()[0] > 0
        
def get_user_email(user_id):
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT email FROM users WHERE user_id = %s;", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None

def save_complaint_to_db(user_id, username, message, category, complaint_text):
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO complaints (user_id, username, message, category, complaint_text, complaint_date)
            VALUES (%s, %s, %s, %s, %s, DEFAULT)
            """,
            (user_id, username, message, category, complaint_text)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка: {e}")

def check_ban(func):
    def wrapper(message_or_call, *args, **kwargs):
        user_id = (message_or_call.from_user.id
                   if hasattr(message_or_call, 'from_user') else message_or_call.message.chat.id)
        if is_user_banned(user_id):
            if hasattr(message_or_call, 'message'):  
                bot.answer_callback_query(
                    message_or_call.id, "❗️ Вы были забанены. Вам не доступны функции бота.", show_alert=True
                )
            else:  
                bot.send_message(message_or_call.chat.id, "❗️ Вы были забанены. Вам не доступны функции бота.")
            return
        return func(message_or_call, *args, **kwargs)

    return wrapper

def check_email(func):
    def wrapper(message_or_call, *args, **kwargs):
        user_id = (message_or_call.from_user.id
                   if hasattr(message_or_call, 'from_user') else message_or_call.message.chat.id)
        email = get_user_email(user_id)
        if not email: 
            if hasattr(message_or_call, 'message'):  
                bot.answer_callback_query(
                    message_or_call.id, "❗️ У вас отсутствует привязанный email. Функции бота недоступны. Введите /set_email, чтобы продолжить.", show_alert=True
                )
            else:  
                bot.send_message(message_or_call.chat.id, "❗️ У вас отсутствует привязанный email. Функции бота недоступны. Введите /set_email, чтобы продолжить.")
            return
        return func(message_or_call, *args, **kwargs)

    return wrapper

def check_user_status_and_execute(user_id, message=None, call=None, action=None):
    if is_user_banned(user_id):
        if message:
            bot.send_message(message.chat.id, "❗️ Вы были забанены. Вам не доступны функции бота.")
        elif call:
            bot.answer_callback_query(call.id, "❗️ Вы были забанены. Вам не доступны функции бота.")
        return False
    else:
        if action:
            if message:
                action(message)
            elif call:
                action(call)
        return True

def is_user_banned(user_id):
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT status FROM users WHERE user_id = %s", (user_id,))
            user_status = cursor.fetchone()
    if user_status and user_status[0] == 'banned':
        return True
    return False

def get_active_users():
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username FROM users WHERE status = 'active';")
            users = cursor.fetchall()
    return users

def get_banned_users():
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username FROM users WHERE status = 'banned';")
            users = cursor.fetchall()
    return users

def ban_user(id):
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET status = 'banned' WHERE id = %s", (id,))
            conn.commit()

def unban_user(id):
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET status = 'active' WHERE id = %s;", (id,))
            conn.commit()


@bot.message_handler(commands=['start'])
@check_ban
def send_welcome(message):
    user_id = message.from_user.id

    if is_user_registered(user_id):
        stored_password = get_user_password(user_id)
        if not stored_password:
            bot.send_message(message.chat.id, "У вас не установлен пароль. Установите его сейчас:")
            bot.register_next_step_handler(message, process_registration)  # Переход к регистрации
        else:
            bot.send_message(message.chat.id, "Введите ваш пароль для входа:")
            bot.register_next_step_handler(message, process_login)
    else:
        markup = types.InlineKeyboardMarkup()
        register_button = types.InlineKeyboardButton("🔒 Регистрация", callback_data="register")
        markup.add(register_button)
        bot.send_message(
            message.chat.id,
            "Добро пожаловать! Для продолжения необходимо зарегистрироваться.",
            reply_markup=markup
        )

def process_login(message):
    user_id = message.from_user.id
    provided_password = message.text
    stored_password = get_user_password(user_id)

    if stored_password and verify_password(stored_password, provided_password):
        if user_id in admin_chat_ids:
            bot.send_message(
                message.chat.id,
                "Вход выполнен успешно! Добро пожаловать в GameHelper, администратор."
            )
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            editor_button = types.KeyboardButton("🖋 Редактор")
            complaint_button = types.KeyboardButton("📩 Жалоба")
            download_button = types.KeyboardButton("📥 Скачать мод")
            compatibility_button = types.KeyboardButton("🖥 Совместимость")
            markup.add(editor_button, complaint_button, download_button, compatibility_button)
        else:
            bot.send_message(
                message.chat.id,
                "Вход выполнен успешно! Добро пожаловать в GameHelper."
            )
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            complaint_button = types.KeyboardButton("📩 Жалоба")
            download_button = types.KeyboardButton("📥 Скачать мод")
            compatibility_button = types.KeyboardButton("🖥 Совместимость")
            markup.add(complaint_button, download_button, compatibility_button)
        
        bot.send_message(
            message.chat.id,
            "Выберите действие из меню ниже. ⬇️",
            reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, "Неверный пароль. Попробуйте снова.")
        bot.register_next_step_handler(message, process_login)

@bot.message_handler(func=lambda message: message.text == "🖋 Редактор")
def handle_editor_mode(message):
    user_id = message.from_user.id

    def editor_mode_action(message):
        if user_id in admin_chat_ids:
            inline_markup = types.InlineKeyboardMarkup()
            inline_markup.add(
                types.InlineKeyboardButton("🛑Забанить пользователя🛑", callback_data="ban_user"),
                types.InlineKeyboardButton("♻Разбанить пользователя♻", callback_data="unban_user")
            )
            inline_markup.add(
                types.InlineKeyboardButton("🟢Добавить новый мод🟢", callback_data="append_mods"),
                types.InlineKeyboardButton("🔴Удалить мод🔴", callback_data="delete_mods")
            )
            inline_markup.add(
                types.InlineKeyboardButton("📰Обьявления📰", callback_data="news_button"),
                types.InlineKeyboardButton("👤Информация о пользователе👤", callback_data="show_users")
            )
            inline_markup.add(
                types.InlineKeyboardButton("🔒Секретная кнопка🔒", callback_data="secret_button")
            )
            inline_markup.add(
                types.InlineKeyboardButton("⬅Назад", callback_data="back_to_welcome")
            )
            sent_message = bot.send_message(
                message.chat.id,
                "🎉 *Режим редактора включен!* 🎉\n\n"
                "Теперь вы можете использовать функции редактирования.\n\n"
                "Выберите действия из меню ниже.",
                parse_mode="Markdown",
                reply_markup=inline_markup
            )
            bot.message_id = sent_message.message_id

    check_user_status_and_execute(user_id, message=message, action=editor_mode_action)

def register_user_with_email(user_id, username, email, message):
    if email_exists(email):  
        bot.send_message(message.chat.id, "❗ Пользователь с данной почтой уже зарегистрирован.")
        return
    
    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (user_id, username, email)
                    VALUES (%s, %s, %s);
                """, (user_id, username, email))
                conn.commit()
        bot.send_message(message.chat.id, "✅ Почта сохранена. Теперь введите пароль:")
        bot.register_next_step_handler(message, lambda msg: set_user_password(user_id, msg.text, msg))
    except Exception as e:
        bot.send_message(message.chat.id, "❗ Ошибка при сохранении данных. Попробуйте снова.")
        print(f"Ошибка регистрации: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "register")
def handle_registration(call):
    bot.send_message(call.message.chat.id, "✉️ Введите ваш email для регистрации:")
    bot.register_next_step_handler(call.message, process_email_input)

def process_email_input(message):
    email = message.text
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):  
        bot.send_message(message.chat.id, "❗ Некорректный формат email. Попробуйте снова:")
        bot.register_next_step_handler(message, process_email_input)
        return
    
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    register_user_with_email(user_id, username, email, message)

def send_registration_success(message, user_id):
    if user_id in admin_chat_ids:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton("🖋 Редактор"),
            types.KeyboardButton("📩 Жалоба"),
            types.KeyboardButton("📥 Скачать мод"),
            types.KeyboardButton("🖥 Совместимость")
        )
        bot.send_message(
            message.chat.id,
            "🎉 *Регистрация прошла успешно!* 🎉\n\n"
            "Теперь вы можете использовать все функции GameHelper.\n\n"
            "Выберите действие из меню ниже. ⬇️",
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton("📩 Жалоба"),
            types.KeyboardButton("📥 Скачать мод"),
            types.KeyboardButton("🖥 Совместимость")
        )
        bot.send_message(
            message.chat.id,
            "🎉 *Регистрация прошла успешно!* 🎉\n\n"
            "Теперь вы можете использовать все функции GameHelper.\n\n"
            "Выберите действие из меню ниже. ⬇️",
            parse_mode="Markdown",
            reply_markup=markup
        )

def process_registration(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    password = message.text

    try:
        register_user(user_id, username)
        set_user_password(user_id, password, message)
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка при регистрации. Попробуйте снова.")
        print(f"Ошибка регистрации: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "ban_user")
def handle_ban_user(call):
    user_id = call.from_user.id

    def ban_user_action(call):
        active_users = get_active_users()
        inline_markup = types.InlineKeyboardMarkup()
        for user in active_users:
            user_id, username = user
            inline_markup.add(
                types.InlineKeyboardButton(f"{username}", callback_data=f"ban_{user_id}")
            )
        inline_markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_editor"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Выберите пользователя для бана:",
            reply_markup=inline_markup
        )

    check_user_status_and_execute(user_id, call=call, action=ban_user_action)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ban_"))
def ban_user_from_button(call):
    user_id = int(call.data.split("_")[1])
    ban_user(user_id)  
    bot.answer_callback_query(call.id, text="Пользователь забанен!")
    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_editor"))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Пользователь забанен. Выберите следующего пользователя или вернитесь в меню.",
        reply_markup=inline_markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "unban_user")
def handle_unban_user(call):
    user_id = call.from_user.id

    def unban_user_action(call):
        banned_users = get_banned_users()
        inline_markup = types.InlineKeyboardMarkup()
        for user in banned_users:
            user_id, username = user
            inline_markup.add(
                types.InlineKeyboardButton(f"{username}", callback_data=f"unban_{user_id}")
            )
        inline_markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_editor"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Выберите пользователя для разбана:",
            reply_markup=inline_markup
        )
    check_user_status_and_execute(user_id, call=call, action=unban_user_action)

@bot.callback_query_handler(func=lambda call: call.data.startswith("unban_"))
def unban_user_from_button(call):
    user_id = int(call.data.split("_")[1])
    unban_user(user_id) 
    bot.answer_callback_query(call.id, text="Пользователь разбанен!")
    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_editor"))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Пользователь разбанен. Выберите следующего пользователя или вернитесь в меню.",
        reply_markup=inline_markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "append_mods")
def new_download_mod(call):  
    inline_markup = types.InlineKeyboardMarkup()
    for game_id, game_name in get_games():
        inline_markup.add(types.InlineKeyboardButton(game_name, callback_data=f"new_{game_id}"))
    inline_markup.add(types.InlineKeyboardButton("⬅Назад", callback_data="back_to_editor"))
    bot.edit_message_text(
        "⬇Выберите игру для добавления мода⬇:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=inline_markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("new_"))
@check_ban
def handle_new_game_selection(call):
    custom_game_id = int(call.data.split("_")[1])
    cursor.execute("SELECT game_name FROM games WHERE game_id = %s", (custom_game_id,))
    game_name = cursor.fetchone()[0]

    markup = types.InlineKeyboardMarkup()
    if game_name == "Minecraft":
        markup.add(
            types.InlineKeyboardButton("Forge", callback_data=f"platform_forge_{custom_game_id}"),
            types.InlineKeyboardButton("Fabric", callback_data=f"platform_fabric_{custom_game_id}")
        )
    else:
        cursor.execute("""
            SELECT mods.mod_id, mods.mod_name, mods.mod_version, mods.mod_file_path
            FROM mods
            WHERE mods.game_id = %s
        """, (custom_game_id,))
        mods = cursor.fetchall()
        for mod_id, mod_name, mod_version, mod_link in mods:
            markup.add(types.InlineKeyboardButton(f"{mod_name} ({mod_version})", url=mod_link))
    
    markup.add(types.InlineKeyboardButton("⬅Назад", callback_data="append_mods"))
    bot.edit_message_text(
        f"⬇Выберите платформу для {game_name}⬇:" if game_name == "Minecraft" else f"⬇Моды для {game_name}⬇:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("platform_"))
@check_ban
def handle_new_platform_selection(call):
    platform, custom_game_id = call.data.split("_")[1:]
    cursor.execute("""
        SELECT DISTINCT mod_version
        FROM mods
        WHERE platform = %s AND game_id = %s
    """, (platform.capitalize(), custom_game_id))
    versions = cursor.fetchall()

    markup = types.InlineKeyboardMarkup()
    for version in versions:
        markup.add(types.InlineKeyboardButton(f"{version[0]}", callback_data=f"select_version_{platform}_{version[0]}_{custom_game_id}"))
    
    markup.add(types.InlineKeyboardButton("⬅Назад", callback_data=f"new_{custom_game_id}"))
    bot.edit_message_text(
        f"⬇Выберите версию для {platform.capitalize()}⬇:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )


waiting_for_mod_name = False
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_version_"))
@check_ban
def handle_mod_version_selection(call):
    global waiting_for_mod_name
    data_parts = call.data.split("_")[2:]

    if len(data_parts) != 3:
        bot.send_message(call.message.chat.id, f"Ошибка в данных! Неправильный формат вызова. Данные: {data_parts}")
        return

    platform, version, custom_game_id = data_parts
    platform = platform.capitalize()

    cursor.execute("SELECT game_name FROM games WHERE game_id = %s", (custom_game_id,))
    game_name = cursor.fetchone()

    if not game_name:
        bot.send_message(call.message.chat.id, "Ошибка: игра с таким ID не найдена.")
        return
    
    waiting_for_mod_name = True
    bot.send_message(call.message.chat.id, f"Введите название мода для версии {version} на платформе {platform}:")
    mod_name_received = False
    process_cancelled = False

    @bot.message_handler(func=lambda message: not mod_name_received)
    def save_mod_name(message):
        global waiting_for_mod_name
        nonlocal mod_name_received, process_cancelled
        mod_name = message.text.strip()

        if message.text.lower() == "отмена" and not process_cancelled:
            bot.send_message(message.chat.id, "Процесс создания мода был отменен.")
            mod_name_received = True
            process_cancelled = True
            return
        cursor.execute("SELECT mod_name FROM mods WHERE mod_name = %s AND game_id = %s", (mod_name, custom_game_id))
        existing_mod = cursor.fetchone()

        if existing_mod:
            bot.send_message(message.chat.id, f"🛑Мод с названием {existing_mod[0]} для игры {game_name[0]} уже существует.🛑 Попробуйте еще раз!")
            return

        cursor.execute("""INSERT INTO mods (mod_name, mod_version, game_id, mod_file_path, platform) VALUES (%s, %s, %s, %s, %s)""", (mod_name, version, custom_game_id, './mods/mod_file.jar', platform))
        conn.commit()
        bot.send_message(message.chat.id, f"Мод {mod_name} для {game_name[0]} (версия {version}) успешно добавлен!")
        waiting_for_mod_name = False
        mod_name_received = True
        bot.send_message(message.chat.id, "Теперь прикрепите файл для мода (например, .jar).")


        @bot.message_handler(content_types=['document'])
        def handle_file(message):
            bot.send_message(message.chat.id, "Загрузка файла подождите... ⏳")  
            file_id = message.document.file_id
            file_info = bot.get_file(file_id)
            file_name = message.document.file_name

            downloaded_file = bot.download_file(file_info.file_path)
            file_path = f'./mods/{file_name}'

            with open(file_path, 'wb') as f:
                f.write(downloaded_file)

            cursor.execute("""UPDATE mods SET mod_file_path = %s WHERE mod_name = %s AND mod_version = %s AND game_id = %s""", (file_path, mod_name, version, custom_game_id))
            conn.commit()

            bot.send_message(message.chat.id, f"✅ Файл для мода {mod_name} успешно загружен! 🎉")

            markup = types.InlineKeyboardMarkup()
            btn_medium = types.InlineKeyboardButton("Medium", callback_data=f"select_compatibility_medium_{mod_name}_{custom_game_id}")
            btn_minimum = types.InlineKeyboardButton("Minimum", callback_data=f"select_compatibility_minimum_{mod_name}_{custom_game_id}")
            markup.add(btn_medium, btn_minimum)
            bot.send_message(message.chat.id, "Выберите совместимость: Medium или Minimum", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_compatibility_"))
def handle_compatibility_selection(call):
    data_parts = call.data.split("_")
    compatibility = data_parts[2]
    mod_name = data_parts[3]
    custom_game_id = data_parts[4]
    cursor.execute("SELECT game_name FROM games WHERE game_id = %s", (custom_game_id,))
    game_name = cursor.fetchone()
    if not game_name:
        bot.send_message(call.message.chat.id, "Ошибка: игра с таким ID не найдена.")
        return
    if compatibility == "medium":
        insert_data = [
            ('Intel+Nvidia', 'Intel Core i5-10400', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium'),
            ('Intel+AMD', 'Intel Core i5-10400', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
            ('AMD+AMD', 'AMD Ryzen 5 3600', 'AMD Radeon RX 580', 8, 40, 'Windows 10', 'Medium'),
            ('AMD+Nvidia', 'AMD Ryzen 5 3600', 'Nvidia GeForce GTX 1660', 8, 40, 'Windows 10', 'Medium')
        ]
    else:  
        insert_data = [
            ('Intel+Nvidia', 'Intel Core i3-8100', 'Nvidia GeForce GTX 1050', 4, 30, 'Windows 10', 'Minimum'),
            ('Intel+AMD', 'Intel Core i3-8100', 'AMD Radeon RX 560', 4, 30, 'Windows 10', 'Minimum'),
            ('AMD+AMD', 'AMD Ryzen 3 2200G', 'AMD Radeon RX 560', 4, 30, 'Windows 10', 'Minimum'),
            ('AMD+Nvidia', 'AMD Ryzen 3 2200G', 'Nvidia GeForce GTX 1050', 4, 30, 'Windows 10', 'Minimum')
        ]
    cursor.execute("SELECT mod_id FROM mods WHERE mod_name = %s AND game_id = %s", (mod_name, custom_game_id))
    mod_id = cursor.fetchone()
    if not mod_id:
        bot.send_message(call.message.chat.id, f"Мод {mod_name} не найден в базе данных для этой игры.")
        return
    for data in insert_data:
        cursor.execute("""
            INSERT INTO mod_requirements (mod_id, cpu_gpu_combination, min_cpu, min_gpu, min_ram, min_storage, supported_os, performance_level)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (mod_id[0], *data))
    
    conn.commit()
    bot.send_message(call.message.chat.id, f"Мод {mod_name} для {game_name[0]} успешно добавлен с совместимостью {compatibility}.")



@bot.callback_query_handler(func=lambda call: call.data == "delete_mods")
def delete_mods(call):  
    inline_markup = types.InlineKeyboardMarkup()
    for game_id, game_name in get_games():
        inline_markup.add(types.InlineKeyboardButton(game_name, callback_data=f"delete_game_{game_id}"))
    inline_markup.add(types.InlineKeyboardButton("⬅Назад", callback_data="back_to_editor"))
    bot.edit_message_text(
        "⬇Выберите игру для удаления мода⬇:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=inline_markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_game_"))
@check_ban
def handle_delete_game_selection(call):
    custom_game_id = int(call.data.split("_")[2])
    cursor.execute("SELECT game_name FROM games WHERE game_id = %s", (custom_game_id,))
    game_name = cursor.fetchone()[0]

    markup = types.InlineKeyboardMarkup()
    if game_name == "Minecraft":
        markup.add(
            types.InlineKeyboardButton("Forge", callback_data=f"delete_platform_forge_{custom_game_id}"),
            types.InlineKeyboardButton("Fabric", callback_data=f"delete_platform_fabric_{custom_game_id}")
        )
    else:
        cursor.execute("""
            SELECT mods.mod_id, mods.mod_name, mods.mod_version
            FROM mods
            WHERE mods.game_id = %s
        """, (custom_game_id,))
        mods = cursor.fetchall()
        for mod_id, mod_name, mod_version in mods:
            markup.add(types.InlineKeyboardButton(f"{mod_name} ({mod_version})", callback_data=f"delete_mod_{mod_id}"))
    
    markup.add(types.InlineKeyboardButton("⬅Назад", callback_data="delete_mods"))
    bot.edit_message_text(
        f"⬇Выберите платформу для удаления модов в {game_name}⬇:" if game_name == "Minecraft" else f"⬇Моды для удаления из {game_name}⬇:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_platform_"))
@check_ban
def handle_delete_platform_selection(call):
    platform_info = call.data.split("_")
    platform = platform_info[2]
    custom_game_id = int(platform_info[3])

    cursor.execute("SELECT game_name FROM games WHERE game_id = %s", (custom_game_id,))
    game_name = cursor.fetchone()[0]

    markup = types.InlineKeyboardMarkup()

    cursor.execute("""
        SELECT DISTINCT mod_version
        FROM mods
        WHERE game_id = %s AND platform = %s
    """, (custom_game_id, platform.capitalize()))
    
    versions = cursor.fetchall()

    for version in versions:
        markup.add(types.InlineKeyboardButton(f" {version[0]}", callback_data=f"delete_version_{platform}_{version[0]}_{custom_game_id}"
        ))

    markup.add(types.InlineKeyboardButton("⬅Назад", callback_data=f"delete_game_{custom_game_id}"))
    bot.edit_message_text(
        f"⬇Выберите версию для удаления модов в {game_name} на платформе {platform}⬇:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_version_"))
@check_ban
def handle_delete_version_selection(call):
    version_info = call.data.split("_")
    platform = version_info[2]
    version = version_info[3]
    custom_game_id = int(version_info[4])

    cursor.execute("SELECT game_name FROM games WHERE game_id = %s", (custom_game_id,))
    game_name = cursor.fetchone()[0]

    markup = types.InlineKeyboardMarkup()
    cursor.execute("""
        SELECT mods.mod_id, mods.mod_name, mods.mod_version
        FROM mods
        WHERE mods.game_id = %s AND mods.platform = %s AND mods.mod_version = %s
    """, (custom_game_id, platform.capitalize(), version))
    
    mods = cursor.fetchall()
    for mod_id, mod_name, mod_version in mods:
         markup.add(types.InlineKeyboardButton(f"{mod_name} ({mod_version})", callback_data=f"delete_mod_{mod_id}"
         ))
    markup.add(types.InlineKeyboardButton("⬅Назад", callback_data=f"delete_platform_{platform}_{custom_game_id}"))
    bot.edit_message_text(
        f"⬇Выберите мод для удаления из {game_name} на платформе {platform}, версия {version}⬇:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_mod_"))
@check_ban
def handle_delete_mod_selection(call):
    mod_id = int(call.data.split("_")[2])
    try:
        cursor.execute("SELECT mod_name, mod_version, mod_file_path, game_id FROM mods WHERE mod_id = %s", (mod_id,))
        mod_info = cursor.fetchone()
        if not mod_info:
            bot.answer_callback_query(call.id, "Мод не найден!")
            return
    
        mod_name, mod_version, mod_file_path, game_id = mod_info
        if mod_file_path and os.path.exists(mod_file_path):
            try:
                os.remove(mod_file_path)
            except Exception as e:
                print(f"Ошибка удаления файла: {e}")
        cursor.execute("DELETE FROM user_downloads WHERE mod_id = %s", (mod_id,))
        cursor.execute("DELETE FROM mods WHERE mod_id = %s", (mod_id,))
        conn.commit()
        bot.answer_callback_query(
            call.id, 
            f"Мод {mod_name} ({mod_version}) был удален!"
        )
        delete_mods(call)
        
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при удалении мода: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка при удалении мода")


@bot.callback_query_handler(func=lambda call: call.data == "news_button")
def handle_news_button(call):
   user_id = call.from_user.id
   
   if user_id not in admin_chat_ids:
       bot.answer_callback_query(call.id, "У вас нет доступа к этой функции!")
       return
   
   if hasattr(bot, 'news_creation_state'):
       del bot.news_creation_state
   
   bot.send_message(
       call.message.chat.id, 
       "📢 Создание нового объявления\n\n"
       "Введите заголовок объявления (до 100 символов):"
   )
   
   bot.register_next_step_handler(call.message, process_news_title)

def process_news_title(message):
   user_id = message.from_user.id

   if len(message.text) > 100:
       bot.send_message(
           message.chat.id, 
           "Заголовок слишком длинный. Введите заголовок до 100 символов:"
       )
       bot.register_next_step_handler(message, process_news_title)
       return
   bot.news_creation_state = {
       'title': message.text,
       'user_id': user_id
   }
   bot.send_message(
       message.chat.id, 
       f"Заголовок: {message.text}\n\n"
       "Введите текст объявления (до 1000 символов):"
   )
   bot.register_next_step_handler(message, process_news_text)

def process_news_text(message):
   if len(message.text) > 1000:
       bot.send_message(
           message.chat.id, 
           "Текст слишком длинный. Введите текст до 1000 символов:"
       )
       bot.register_next_step_handler(message, process_news_text)
       return

   confirm_markup = types.InlineKeyboardMarkup()
   confirm_markup.add(
       types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_news"),
       types.InlineKeyboardButton("❌ Отменить", callback_data="cancel_news")
   )

   bot.news_creation_state.update({
       'text': message.text
   })

   preview_message = (
       "📢 *Предварительный просмотр объявления* 📢\n\n"
       f"*{bot.news_creation_state['title']}*\n\n"
       f"{message.text}"
   )
   
   bot.send_message(
       message.chat.id, 
       preview_message,
       parse_mode="Markdown",
       reply_markup=confirm_markup
   )

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_news", "cancel_news"])
def handle_news_confirmation(call):
    if call.data == "cancel_news":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Создание объявления отменено."
        )
        if hasattr(bot, 'news_creation_state'):
            del bot.news_creation_state
        return

    if call.data == "confirm_news":
        if not hasattr(bot, 'news_creation_state'):
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="⚠️ Состояние новости утеряно. Попробуйте снова."
            )
            return

        news_state = bot.news_creation_state

        try:
            cursor.execute("SELECT user_id FROM users")
            users = cursor.fetchall()

            sent_count = 0
            failed_count = 0

            for (user_id,) in users:
                try:
                    bot.send_message(
                        user_id,
                        f"📢 *{news_state['title']}* 📢\n\n{news_state['text']}",
                        parse_mode="Markdown"
                    )
                    sent_count += 1
                except Exception as e:
                    failed_count += 1
                    print(f"Ошибка отправки новости пользователю {user_id}: {e}")

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"✅ Новость успешно отправлена!"
            )

            del bot.news_creation_state

        except Exception as e:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"❌ Ошибка при рассылке: {str(e)}"
            )
            print(f"Ошибка при рассылке новости: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "show_users")
def show_users(call):
    users = get_all_users()
    inline_markup = types.InlineKeyboardMarkup()
    for user in users:
        inline_markup.add(
            types.InlineKeyboardButton(f"{user['username']}", callback_data=f"{user['user_id']}")
        )
    inline_markup.add(types.InlineKeyboardButton("⬅️Назад", callback_data="back_to_editor"))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Выберите пользователя для получения информации:",
        reply_markup=inline_markup
    )

@bot.callback_query_handler(func=lambda call: call.data.isdigit())
def show_user_info(call):
    inline_markup = types.InlineKeyboardMarkup()
    try:
        user_id = int(call.data)
        cursor.execute(
            "SELECT username, user_id, registration_date FROM users WHERE user_id = %s",
            (user_id,)
        )
        user_data = cursor.fetchone()
        if user_data:
            username, user_id, registration_date = user_data
            text = (
                f"Информация о пользователе @{username}:\n"
                f"🆔 ID пользователя: {user_id}\n"
                f"📅 Дата регистрации: {registration_date}\n"
            )
            inline_markup.add(types.InlineKeyboardButton(f"🔑 Сбросить пароль {username}", callback_data=f"reset_password_{user_id}"))
            inline_markup.add(types.InlineKeyboardButton(f"✉️ Сбросить почту {username}", callback_data=f"reset_email_{user_id}"))
            inline_markup.add(types.InlineKeyboardButton("⬅️Назад", callback_data="back_to_editor"))
        else:
            text = "Пользователь не найден."
            inline_markup.add(types.InlineKeyboardButton("⬅️Назад", callback_data="back_to_editor"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=inline_markup
        )
    except Exception as e:
        bot.answer_callback_query(call.id, text="Произошла ошибка.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reset_password_"))
def handle_reset_password(call):
    user_id = int(call.data.split("_")[2])  
    username = call.message.text.split("\n")[0].split("@")[1] 
    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET password = NULL WHERE user_id = %s",
                    (user_id,)
                )
                conn.commit()
        bot.send_message(
            call.message.chat.id,
            f"✅ Пароль для пользователя @{username} был сброшен. Пользователь должен установить новый пароль."
        )
        bot.send_message(
            user_id,
            f"❗️ Ваш пароль был сброшен администратором. Пожалуйста, установите новый пароль.\nВведите /set_password, чтобы продолжить."
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ Произошла ошибка при сбросе пароля.")
        print(f"Ошибка сброса пароля: {e}")

@bot.message_handler(commands=['set_password'])
def set_password(message):
    user_id = message.from_user.id

    stored_password = get_user_password(user_id)

    if stored_password is None:  
        bot.send_message(
            message.chat.id,
            "Введите новый пароль:"
        )
        bot.register_next_step_handler(message, save_new_password)
    else:
        bot.send_message(
            message.chat.id,
            "❌ У вас уже установлен пароль. Если вы хотите изменить его, обратитесь к администратору"
        )

def save_new_password(message):
    user_id = message.from_user.id
    new_password = message.text
    if message.content_type != 'text':
        bot.send_message(
            message.chat.id,
            "❌ Пароль должен быть текстовым сообщением. Пожалуйста, введите пароль снова:"
        )
        bot.register_next_step_handler(message, save_new_password)
        return

    try:
        is_valid, validation_message = validate_password(new_password)
        if not is_valid:
            bot.send_message(
                message.chat.id,
                f"❌ {validation_message} Пожалуйста, введите пароль снова:"
            )
            bot.register_next_step_handler(message, save_new_password)
            return
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(new_password.encode(), salt)

        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET password = %s WHERE user_id = %s",
                    (hashed_password, user_id)
                )
                conn.commit()

        bot.send_message(
            message.chat.id,
            "✅ Ваш новый пароль успешно установлен!"
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при установке нового пароля. Попробуйте снова."
        )
        print(f"Ошибка установки нового пароля: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reset_email_"))
def handle_reset_email(call):
    user_id = int(call.data.split("_")[2])
    username = call.message.text.split("\n")[0].split("@")[1]
    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET email = NULL WHERE user_id = %s",
                    (user_id,)
                )
                conn.commit()
        bot.send_message(
            call.message.chat.id,
            f"✅ Почта для пользователя @{username} была сброшена. Пользователь должен установить новую почту."
        )
        bot.send_message(
            user_id,
            f"❗️ Ваша почта была сброшена администратором. Пожалуйста, установите новую почту.\nВведите /set_email, чтобы продолжить."
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ Произошла ошибка при сбросе почты.")
        print(f"Ошибка сброса почты: {e}")

@bot.message_handler(commands=['set_email'])
def set_email(message):
    user_id = message.from_user.id
    bot.send_message(
        message.chat.id,
        "✉️ Введите новый email:"
    )
    bot.register_next_step_handler(message, validate_email, user_id)

def validate_email(message, user_id):
    email = message.text.strip()
    if not email or "@" not in email:
        bot.send_message(
            message.chat.id,
            "❌ Неверный формат почты. Пожалуйста, введите корректный email."
        )
        bot.register_next_step_handler(message, validate_email, user_id)
        return
    
    if not any(email.endswith(domain) for domain in ALLOWED_DOMAINS):
        allowed_domains_text = "\n".join(ALLOWED_DOMAINS)
        bot.send_message(
            message.chat.id,
            f"❌ Почта должна использовать один из следующих доменов:\n{allowed_domains_text}"
        )
        bot.register_next_step_handler(message, validate_email, user_id)
        return
    
    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT email FROM users WHERE email = %s", 
                    (email,)
                )
                existing_email = cursor.fetchone()
                
                if existing_email:
                    bot.send_message(
                        message.chat.id,
                        "❌ Почта уже используется другим пользователем. Пожалуйста, введите другую почту:"
                    )
                    bot.register_next_step_handler(message, validate_email, user_id)
                    return
                cursor.execute(
                    "UPDATE users SET email = %s WHERE user_id = %s",
                    (email, user_id)
                )
                conn.commit()

        bot.send_message(
            message.chat.id,
            f"✅ Ваша почта успешно обновлена на {email}."
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при обновлении почты. Попробуйте снова позже."
        )
        print(f"Ошибка при обновлении почты: {e}")
def save_new_email(message):
    user_id = message.from_user.id
    new_email = message.text
    if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
        bot.send_message(
            message.chat.id,
            "❌ Некорректный формат email. Пожалуйста, введите корректный email снова:"
        )
        bot.register_next_step_handler(message, save_new_email)
        return
    try:
        if email_exists(new_email):
            bot.send_message(
                message.chat.id,
                "❌ Этот email уже используется. Введите другой email:"
            )
            bot.register_next_step_handler(message, save_new_email)
            return
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET email = %s WHERE user_id = %s",
                    (new_email, user_id)
                )
                conn.commit()

        bot.send_message(
            message.chat.id,
            "✅ Ваш новый email успешно сохранен!"
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при сохранении нового email. Попробуйте снова."
        )
        print(f"Ошибка установки новой почты: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "secret_button")
def handle_secret_button(call):
    user_id = call.from_user.id
    if user_id in admin_chat_ids:
        msg = bot.send_message(call.message.chat.id, "🔐 Введите пароль:")
        bot.register_next_step_handler(msg, verify_secret_password)
    else:
        bot.answer_callback_query(call.id, "Вы не админ.", show_alert=True)


def verify_secret_password(message):
    entered_password = message.text.lower()
    correct_password = "12345" 
    if entered_password == correct_password:
        inline_markup = types.InlineKeyboardMarkup()
        inline_markup.add(
            types.InlineKeyboardButton("✅Подтвердить", callback_data="confirm_destruction"),
            types.InlineKeyboardButton("⬅Назад", callback_data="back_to_editor")
        )
        bot.send_message(
            message.chat.id,
            "❗🆘*Внимание!*🆘❗\n\n"
            "Данная функция уничтожает все данные бота.\n\n"
            "Вы действительно хотите продолжить?",
            parse_mode="Markdown",
            reply_markup=inline_markup
        )
    else:
        bot.send_message(message.chat.id, "❌ Пароль неправильный. Вы не админ.")

@bot.callback_query_handler(func=lambda call: call.data == "confirm_destruction")
def total_verify(call):
    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(
        types.InlineKeyboardButton("Да", callback_data="total_confirm"),
        types.InlineKeyboardButton("Нет", callback_data="back_to_editor")
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="❗*Процесс уничтожения необратим!*❗\n\n"
             "Вы точно уверены?",
        parse_mode="Markdown",
        reply_markup=inline_markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "total_confirm")
def drop_all_tables(call):
    try:
        drop_queries = [
            "DROP TABLE IF EXISTS mod_compatibility CASCADE;",
            "DROP TABLE IF EXISTS user_downloads CASCADE;", 
            "DROP TABLE IF EXISTS complaints CASCADE;",  
            "DROP TABLE IF EXISTS mods CASCADE;", 
            "DROP TABLE IF EXISTS games CASCADE;", 
            "DROP TABLE IF EXISTS user_computers CASCADE;", 
            "DROP TABLE IF EXISTS mod_requirements CASCADE;", 
            "DROP TABLE IF EXISTS users CASCADE;", 
            "DROP TABLE IF EXISTS hardware_components CASCADE;"
        ]
        with conn.cursor() as cursor:
            for query in drop_queries:
                cursor.execute(query)
            conn.commit()  
        bot.send_message(call.message.chat.id, "✅Все данные успешно удалены. Бот уничтожен и был отключен☺✅")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка при удалении данных: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_editor")
def handle_back_to_editor(call):
    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(
                types.InlineKeyboardButton("🛑Забанить пользователя🛑", callback_data="ban_user"),
                types.InlineKeyboardButton("♻Разбанить пользователя♻", callback_data="unban_user")
            )
    inline_markup.add(
                types.InlineKeyboardButton("🟢Добавить новый мод🟢", callback_data="append_mods"),
                types.InlineKeyboardButton("🔴Удалить мод🔴", callback_data="delete_mods")
            )
    inline_markup.add(
                types.InlineKeyboardButton("📰Обьявления📰", callback_data="news_button"),
                types.InlineKeyboardButton("👤Информация о пользователе👤", callback_data="show_users")
            )
    inline_markup.add(
                types.InlineKeyboardButton("🔒Секретная кнопка🔒", callback_data="secret_button")
            )
    inline_markup.add(
                types.InlineKeyboardButton("⬅Назад", callback_data="back_to_welcome")
            )
    bot.edit_message_text(
        "🎉 *Режим редактора включен!* 🎉\n\n"
        "Теперь вы можете использовать функции редактирования.\n\n"
        "Выберите действия из меню ниже.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,  
        parse_mode="Markdown",
        reply_markup=inline_markup
    )

# Обработчик команды /info
@bot.message_handler(commands=['info'])
@check_ban
@check_email
def send_info(message):
    bot.send_message(
        message.chat.id,
        "ℹ️ *Информация о боте GameHelper* ℹ️\n\n"
        "GameHelper помогает вам скачивать моды для игр, сообщать об ошибках и оставлять жалобы. "
        "Вы можете воспользоваться следующими функциями:\n\n"
        "1️⃣ Скачать моды для игр.\n"
        "2️⃣ Оставить жалобу на неисправный мод или неверную инструкцию.\n"
        "3️⃣ Найти информацию о нужных модах.\n\n"
        "Используйте /help для получения списка команд.",
        parse_mode="Markdown"
    )

# Обработчик команды /help
@bot.message_handler(commands=['help'])
@check_ban
@check_email
def send_help(message):
    bot.send_message(
        message.chat.id,
        "❓ *Список доступных команд:* ❓\n\n"
        "🔹 /start - Перезапуск бота.\n"
        "🔹 /info - Узнать больше о боте.\n"
        "🔹 /help - Список команд.\n\n"
        "Дополнительные функции доступны через меню ниже. 👇",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text == "📩 Жалоба")
@check_ban
@check_email
def handle_complaint(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📛 Мод не работает", callback_data="complaint_mod_error"),
        types.InlineKeyboardButton("📺 Проблема с инструкцией", callback_data="complaint_instructions"),
        types.InlineKeyboardButton("❓ Другие проблемы", callback_data="complaint_other")
    )
    markup.add(types.InlineKeyboardButton("⬅Назад", callback_data="back_to_welcome"))
    bot.send_message(
        message.chat.id,
        "😟 *О нет! У вас возникла жалоба?* 😟\n\n"
        "Пожалуйста, выберите тип вашей жалобы из предложенных вариантов:\n"
        "Выберите категорию:",
        parse_mode="Markdown", reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("complaint"))
@check_ban
@check_email
def handle_complaint_category(call):
    if call.data == "complaint_mod_error":
        bot.send_message(call.message.chat.id, "Опишите проблему с модом. Мы обязательно рассмотрим вашу жалобу.")
        bot.register_next_step_handler(call.message, process_complaint, message_column_value="📛 Мод не работает")
    elif call.data == "complaint_instructions":
        bot.send_message(call.message.chat.id, "Опишите проблему, связанную с инструкцией. Мы обязательно рассмотрим вашу жалобу.")
        bot.register_next_step_handler(call.message, process_complaint, message_column_value="📺 Проблема с инструкцией")
    elif call.data == "complaint_other":
        bot.send_message(call.message.chat.id, "Опишите вашу проблему. Мы постараемся помочь!")
        bot.register_next_step_handler(call.message, process_complaint, message_column_value="❓ Другие проблемы")
def process_complaint(message, message_column_value):
    username = message.from_user.username or "Без имени"
    user_id = message.chat.id
    category = None
    media_type = None
    media_id = None
    if message.text:
        category = "Текст"
        complaint_text = message.text
    elif message.photo:
        category = "Фото"
        media_type = "photo"
        media_id = message.photo[-1].file_id
        complaint_text = message.caption or None
    elif message.animation:
        category = "GIF"
        media_type = "animation"
        media_id = message.animation.file_id
        complaint_text = message.caption or None
    elif message.voice:
        category = "Голосовое сообщение"
        media_type = "voice"
        media_id = message.voice.file_id
        complaint_text = None
    elif message.video:
        category = "Видео"
        media_type = "video"
        media_id = message.video.file_id
        complaint_text = message.caption or None
    elif message.video_note:
        bot.send_message(message.chat.id, "❌ Жалобы в формате видео-кружков не принимаются.")
        return
    elif message.sticker:
        bot.send_message(message.chat.id, "❌ Жалобы в формате стикеров не принимаются.")
        return
    save_complaint_to_db(user_id, username, message_column_value, category, complaint_text)
    notify_admins(user_id=user_id, username=username, category=category, message_column_value=message_column_value, complaint_text=complaint_text, media_type=media_type, media_id=media_id,
    )
    bot.send_message(message.chat.id, "Ваша жалоба отправлена. Спасибо за обратную связь!")
def notify_admins(user_id, username, category, message_column_value, complaint_text, media_type=None, media_id=None):
    for admin_chat_id in admin_chat_ids:
        if media_type is None:  
            admin_message = (
                f"❗️ Новая жалоба от пользователя @{username} (ID: {user_id}):\n"
                f"Категория: {category}\n"
                f"Тип жалобы: {message_column_value}\n"
                f"Текст жалобы: {complaint_text or 'Не указан'}"
            )
            bot.send_message(admin_chat_id, admin_message)
        elif media_type == "photo":
            bot.send_photo(admin_chat_id, media_id,
                caption=(
                    f"❗️ Новая жалоба от пользователя @{username} (ID: {user_id}):\n"
                    f"Категория: {category}\n"
                    f"Тип жалобы: {message_column_value}\n"
                    f"Описание: {complaint_text or 'Не указано'}"),
            )
        elif media_type == "video":
            bot.send_video(admin_chat_id, media_id,
                caption=(
                    f"❗️ Новая жалоба от пользователя @{username} (ID: {user_id}):\n"
                    f"Категория: {category}\n"
                    f"Тип жалобы: {message_column_value}\n"
                    f"Описание: {complaint_text or 'Не указано'}"),
            )
        elif media_type == "voice":
            bot.send_voice(admin_chat_id, media_id,
                caption=(
                    f"❗️ Новая жалоба от пользователя @{username} (ID: {user_id}):\n"
                    f"Категория: {category}\n"
                    f"Тип жалобы: {message_column_value}\n"),
            )
        elif media_type == "animation":
            bot.send_animation(admin_chat_id, media_id,
                caption=(
                    f"❗️ Новая жалоба от пользователя @{username} (ID: {user_id}):\n"
                    f"Категория: {category}\n"
                    f"Тип жалобы: {message_column_value}\n"
                    f"Описание: {complaint_text or 'Не указано'}"),
            )
def get_games():
    cursor.execute("SELECT game_id, game_name FROM games")
    return cursor.fetchall()
def log_user_download(user_id, mod_id, mod_version):
    try:
        cursor.execute("""
            SELECT 1
            FROM user_downloads
            WHERE user_id = %s AND mod_id = %s AND mod_version = %s
        """, (user_id, mod_id, mod_version))
        
        result = cursor.fetchone()
    
        if result:
            pass
        else:
            cursor.execute("""
                INSERT INTO user_downloads (user_id, mod_id, mod_version, download_date)
                VALUES (%s, %s, %s, DEFAULT)
            """, (user_id, mod_id, mod_version))

            conn.commit()
    except Exception as e:
        print(f"Ошибка записи скачивания: {e}")

@bot.message_handler(func=lambda message: message.text == "📥 Скачать мод")
@check_ban
@check_email
def handle_download_mod(message):
    markup = types.InlineKeyboardMarkup()
    for game_id, game_name in get_games():
        markup.add(types.InlineKeyboardButton(game_name, callback_data=f"game_{game_id}"))
    markup.add(types.InlineKeyboardButton("⬅Назад", callback_data="back_to_welcome"))
    bot.send_message(
        message.chat.id,
        "⬇Выберите игру для скачивания мода⬇:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
@check_ban
@check_email
def handle_game_selection(call):
    game_id = int(call.data.split("_")[1])
    cursor.execute("SELECT game_name FROM games WHERE game_id = %s", (game_id,))
    game_name = cursor.fetchone()[0]

    if game_name == "Minecraft":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Forge", callback_data=f"minecraft_forge_{game_id}"),
            types.InlineKeyboardButton("Fabric", callback_data=f"minecraft_fabric_{game_id}")
        )
        markup.add(types.InlineKeyboardButton("⬅Назад", callback_data="back_to_mods"))
        bot.edit_message_text(
            f"⬇Выберите платформу для {game_name}⬇:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )
    else:
        cursor.execute("""
            SELECT mods.mod_id, mods.mod_name, mods.mod_version, mods.mod_file_path
            FROM mods
            WHERE mods.game_id = %s
        """, (game_id,))
        mods = cursor.fetchall()
        markup = types.InlineKeyboardMarkup()
        for mod_id, mod_name, mod_version, mod_link in mods:
            markup.add(types.InlineKeyboardButton(f"{mod_name} ({mod_version})", url=mod_link))
        markup.add(types.InlineKeyboardButton("⬅Назад", callback_data="back_to_mods"))
        bot.edit_message_text(
            f"⬇Моды для {game_name}⬇:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("minecraft_"))
@check_ban
@check_email
def handle_minecraft_platform(call):
    platform, game_id = call.data.split("_")[1:]
    versions = {
        "forge": ["1.12.2", "1.16.5", "1.20.1"],
        "fabric": ["1.12.2", "1.16.5", "1.20.1"]
    }
    markup = types.InlineKeyboardMarkup()
    for version in versions[platform]:
        markup.add(types.InlineKeyboardButton(version, callback_data=f"{platform}_{version}_{game_id}"))
    markup.add(types.InlineKeyboardButton("⬅Назад", callback_data=f"game_{game_id}"))
    bot.edit_message_text(
        f"⬇Выберите версию для {platform.capitalize()}⬇:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

# Обработчик выбора версии
@bot.callback_query_handler(func=lambda call: call.data.split("_")[0] in ["forge", "fabric"])
@check_ban
@check_email
def handle_version_selection(call):
    platform, version, game_id = call.data.split("_")
    cursor.execute("""
        SELECT mods.mod_id, mods.mod_name, mods.mod_version, mods.mod_file_path
        FROM mods
        JOIN games ON mods.game_id = games.game_id
        WHERE games.game_id = %s AND mods.platform = %s AND mods.mod_version = %s
    """, (game_id, platform.capitalize(), version))
    mods = cursor.fetchall()

    if not mods:
        bot.edit_message_text(
            "❌ Моды для выбранной платформы и версии не найдены.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        return

    markup = types.InlineKeyboardMarkup()
    for mod_id, mod_name, mod_version, mod_file_path in mods:
        markup.add(types.InlineKeyboardButton(f"{mod_name} ({mod_version})", callback_data=f"download_{mod_id}"))

    markup.add(types.InlineKeyboardButton("⬅Назад", callback_data=f"minecraft_{platform}_{game_id}"))
    bot.edit_message_text(
        f"⬇Моды для {platform.capitalize()} {version}:⬇",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("download_"))
@check_ban
@check_email
def handle_mod_download(call):
    mod_id = int(call.data.split("_")[1])
    cursor.execute("""
        SELECT mod_name, mod_version, mod_file_path
        FROM mods
        WHERE mod_id = %s
    """, (mod_id,))
    mod_info = cursor.fetchone()
    if not mod_info:
        bot.answer_callback_query(call.id, "❌ Мод не найден.")
        return
    mod_name, mod_version, mod_file_path = mod_info
    log_user_download(call.from_user.id, mod_id, mod_version)
    loading_message = bot.send_message(call.message.chat.id, "🔄 Загрузка мода, подождите...")
    if os.path.exists(mod_file_path):
        try:
            with open(mod_file_path, 'rb') as mod_file:
                bot.send_document(call.message.chat.id, mod_file, caption=f"Вот ваш мод: {mod_name} ({mod_version})")
            bot.edit_message_text(
                f"✅ Мод {mod_name} ({mod_version}) успешно отправлен!",
                chat_id=call.message.chat.id,
                message_id=loading_message.message_id
            )
        except Exception as e:
            bot.edit_message_text(
                f"❌ Произошла ошибка при отправке мода: {e}",
                chat_id=call.message.chat.id,
                message_id=loading_message.message_id
            )
    else:
        bot.edit_message_text(
            f"❌ Извините, файл для мода {mod_name} ({mod_version}) не найден на сервере.",
            chat_id=call.message.chat.id,
            message_id=loading_message.message_id
        )

# Обработчики для кнопки "Назад"
@bot.callback_query_handler(func=lambda call: call.data == "back_to_mods")
@check_ban
@check_email
def handle_back_to_mods(call):
    markup = types.InlineKeyboardMarkup()
    for game_id, game_name in get_games():
        markup.add(types.InlineKeyboardButton(game_name, callback_data=f"game_{game_id}"))
    markup.add(types.InlineKeyboardButton("⬅Назад", callback_data="back_to_welcome"))
    bot.edit_message_text(
        "⬇Выберите игру для скачивания мода⬇:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

# Сохранение данных пользователя временно
bot_data = {}

@bot.message_handler(commands=['set_computer'])
@check_ban
@check_email
def set_computer(message):
    user_id = message.from_user.id

    cursor.execute("""
        SELECT 1
        FROM user_computers
        WHERE user_id = %s
    """, (user_id,))
    user_exists = cursor.fetchone()

    if user_exists:
        bot.send_message(
            message.chat.id,
            "❌ У вас уже есть созданный компьютер. Используйте /set_update_computer, чтобы обновить данные."
        )
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Intel", callback_data="cpu_Intel"),
            types.InlineKeyboardButton("AMD", callback_data="cpu_AMD")
        )
        bot.send_message(
            message.chat.id,
            "Выберите производителя процессора:",
            reply_markup=markup
        )

@bot.message_handler(commands=['set_update_computer'])
@check_ban
@check_email
def set_update_computer(message):
    user_id = message.from_user.id
    cursor.execute("""
        SELECT 1
        FROM user_computers
        WHERE user_id = %s
    """, (user_id,))
    user_exists = cursor.fetchone()

    if not user_exists:
        bot.send_message(
            message.chat.id,
            "❌ У вас ещё нет созданного компьютера. Используйте /set_computer, чтобы создать новый."
        )
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Intel", callback_data="cpu_Intel_update"),
            types.InlineKeyboardButton("AMD", callback_data="cpu_AMD_update")
        )
        bot.send_message(
            message.chat.id,
            "Выберите производителя процессора для обновления данных:",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("cpu_"))
@check_ban
@check_email
def handle_cpu_selection(call):
    cpu_manufacturer = call.data.split("_")[1]
    bot_data[call.from_user.id] = {"cpu": cpu_manufacturer}

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Nvidia", callback_data="gpu_Nvidia"),
        types.InlineKeyboardButton("AMD", callback_data="gpu_AMD")
    )
    bot.edit_message_text(
        "Выберите производителя видеокарты:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("gpu_"))
@check_ban
@check_email
def handle_gpu_selection(call):
    gpu_manufacturer = call.data.split("_")[1]
    user_id = call.from_user.id

    bot_data[user_id]["gpu"] = gpu_manufacturer
    cpu = bot_data[user_id]["cpu"]

    cursor.execute("""
        SELECT cpu_model, gpu_model, performance_level, description
        FROM hardware_components
        WHERE cpu_manufacturer = %s AND gpu_manufacturer = %s
    """, (cpu, gpu_manufacturer))
    configs = cursor.fetchall()

    if not configs:
        bot.send_message(call.message.chat.id, "❌ Данные для выбранной комбинации не найдены.")
        return

    markup = types.InlineKeyboardMarkup()
    for cpu_model, gpu_model, level, description in configs:
        markup.add(
            types.InlineKeyboardButton(
                f"{cpu_model} + {gpu_model}",
                callback_data=f"final_{cpu_model}_{gpu_model}_{level}"
            )
        )

    bot.send_message(
        call.message.chat.id,
        "Выберите примерные компоненты компьютера из списка. Это примерные данные: "
        "если ваши компоненты лучше минимальных, но хуже средних, выберите минимальные.",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("final_"))
@check_ban
@check_email
def handle_final_selection(call):
    _, cpu_model, gpu_model, level = call.data.split("_")
    user_id = call.from_user.id

    cursor.execute("""
        INSERT INTO user_computers (user_id, cpu_model, gpu_model, performance_level)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET cpu_model = EXCLUDED.cpu_model, gpu_model = EXCLUDED.gpu_model, performance_level = EXCLUDED.performance_level;
    """, (user_id, cpu_model, gpu_model, level))
    conn.commit()

    bot.send_message(
        call.message.chat.id,
        f"✅ Вы выбрали:\nCPU: {cpu_model}\nGPU: {gpu_model}\nУровень: {level}\nТеперь можно проверить совместимость модов."
    )

@bot.message_handler(func=lambda message: message.text == "🖥 Совместимость")
@check_ban
@check_email
def handle_compatibility(message):
    user_id = message.from_user.id

    cursor.execute("""
        SELECT 1
        FROM user_computers
        WHERE user_id = %s
    """, (user_id,))
    user_exists = cursor.fetchone()

    if not user_exists:
        bot.send_message(message.chat.id, "❌ У вас ещё нет созданного компьютера. Используйте /set_computer.")
        return

    cursor.execute("""
        SELECT m.mod_id, m.mod_name, m.mod_version
        FROM user_downloads ud
        JOIN mods m ON ud.mod_id = m.mod_id
        WHERE ud.user_id = %s
    """, (user_id,))
    downloads = cursor.fetchall()

    if not downloads:
        bot.send_message(message.chat.id, "❌ У вас ещё нет скачанных модов.")
        return

    markup = types.InlineKeyboardMarkup()
    for mod_id, mod_name, mod_version in downloads:
        markup.add(types.InlineKeyboardButton(f"{mod_name} ({mod_version})", callback_data=f"check_{mod_id}"))

    bot.send_message(
        message.chat.id,
        "⬇ Выберите мод для проверки совместимости.\n\n"
        "Хотите обновить компьютер? Используйте команду /set_update_computer",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("check_"))
@check_ban
@check_email
def handle_check_compatibility(call):
    mod_id = int(call.data.split("_")[1])
    user_id = call.from_user.id

    cursor.execute("""
        SELECT performance_level
        FROM user_computers
        WHERE user_id = %s
    """, (user_id,))
    user_computer = cursor.fetchone()

    if not user_computer:
        bot.send_message(call.message.chat.id, "❌ Данные о вашем компьютере не найдены. Используйте /set_computer, чтобы добавить их.")
        return

    user_level = user_computer[0]  

    cursor.execute("""
        SELECT mod_name, performance_level
        FROM mods
        JOIN mod_requirements ON mods.mod_id = mod_requirements.mod_id
        WHERE mods.mod_id = %s
    """, (mod_id,))
    mod_info = cursor.fetchone()

    if not mod_info:
        bot.send_message(call.message.chat.id, "❌ Требования для этого мода не найдены.")
        return

    mod_name, mod_level = mod_info

    levels = {"Minimum": 1, "Medium": 2, "Maximum": 3}
    if levels[user_level] >= levels[mod_level]:
        bot.send_message(
            call.message.chat.id,
            f"✅ Ваш компьютер полностью подходит для мода {mod_name}.\n"
            f"Требуемый уровень: {mod_level}\nВаш уровень: {user_level}."
        )
    else:
        bot.send_message(
            call.message.chat.id,
            f"❌ Ваш компьютер не соответствует требованиям мода {mod_name}.\n"
            f"Требуемый уровень: {mod_level}\nВаш уровень: {user_level}."
        )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_welcome")
@check_ban
@check_email
def handle_back_to_welcome(call):
    bot.edit_message_text(
        "Вы вернулись назад 🎉\n\n"
        "🎉 Добро пожаловать в наш  телеграмм бот 🎉\n\n"
        "Выберите действие из меню ниже. ⬇️",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )
    
@bot.message_handler(func=lambda message: not waiting_for_mod_name)
def handle_unknown(message):
    bot.send_message(message.chat.id, "Непонятная команда. Введите команду /help.")

bot.polling(none_stop=True, interval=0)