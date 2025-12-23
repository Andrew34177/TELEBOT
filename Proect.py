import telebot
import json
import os
from openai import OpenAI

# Настройка клиента OpenAI
client = OpenAI(
    api_key="io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjRlMDAzMGQzLWMzMDYtNGU3NC1iZWUxLTEzYjAxYTg2NWE5MSIsImV4cCI6NDkxODg1MzIxOX0.AxRVKHeKHze_ESqYm1eQzZnYjSAwCnFiwoWVe3XKA-qN8UiHW0EHUK0kfL1olNzuli1QUHKqxQ-q1suMUe7AuQ",
    base_url="https://api.intelligence.io.solutions/api/v1/",
)

# Токен бота
bot = telebot.TeleBot("8312236904:AAEYs9SF6ySyg-JqRNjJYO_UDm4bkmxvv5M")

# Файлы для хранения данных
JSON_FILE = "../characters.json"
CHAT_FILE = "../chat_history.json"


# Загрузка данных из JSON
def load_data(filename):
    """Загружает данные из JSON файла"""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


# Сохранение данных в JSON
def save_data(filename, data):
    """Сохраняет данные в JSON файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Загрузка при старте
characters = load_data(JSON_FILE)
chat_history = load_data(CHAT_FILE)


# Функция для общения с ИИ
def get_ai_response(user_message, character_data=None):
    """Получает ответ от ИИ"""
    try:
        # Если есть персонаж, используем его данные
        if character_data:
            prompt = f"""Ты - персонаж по имени {character_data['name']}.
Тебе {character_data['age']} лет. Ты {character_data['job']}.

Ты разговариваешь с человеком как реальный друг.
Не говори, что ты ИИ или бот.
Отвечай естественно, как настоящий человек.
Будь дружелюбным и интересным собеседником.

Сообщение от человека: {user_message}"""
        else:
            prompt = f"Ты дружелюбный помощник. Отвечай естественно. Сообщение: {user_message}"

        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.8,
            stream=False,
            max_tokens=400
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Ошибка: {str(e)}"


# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    text = """
Привет! Я бот для общения с персонажами.

Команды:
/create - создать персонажа
/mychar - посмотреть персонажа
/edit - изменить персонажа
/delete - удалить персонажа

Просто напиши сообщение - и я отвечу!
    """
    bot.reply_to(message, text)


# Создание персонажа
@bot.message_handler(commands=['create'])
def create_character(message):
    user_id = str(message.from_user.id)

    if user_id in characters:
        character = characters[user_id]
        bot.reply_to(message,
                     f"У тебя уже есть персонаж:\nИмя: {character['name']}\nВозраст: {character['age']}\nЗанятие: {character['job']}")
        return

    msg = bot.reply_to(message, "Напиши имя персонажа:")
    bot.register_next_step_handler(msg, get_name)


def get_name(message):
    user_id = str(message.from_user.id)
    name = message.text.strip()

    characters[user_id] = {
        "name": name,
        "age": "",
        "job": ""
    }
    save_data(JSON_FILE, characters)

    msg = bot.reply_to(message, f"Имя сохранено: {name}\n\nНапиши возраст персонажа:")
    bot.register_next_step_handler(msg, get_age)


def get_age(message):
    user_id = str(message.from_user.id)
    age = message.text.strip()

    characters[user_id]["age"] = age
    save_data(JSON_FILE, characters)

    msg = bot.reply_to(message, f"Возраст сохранен: {age}\n\nЧем занимается персонаж?")
    bot.register_next_step_handler(msg, get_job)


def get_job(message):
    user_id = str(message.from_user.id)
    job = message.text.strip()

    characters[user_id]["job"] = job
    save_data(JSON_FILE, characters)

    character = characters[user_id]
    result = f"""
Персонаж создан!

Имя: {character['name']}
Возраст: {character['age']}
Занятие: {character['job']}

Теперь просто пиши сообщения!
    """

    bot.reply_to(message, result)


# Посмотреть персонажа
@bot.message_handler(commands=['mychar'])
def my_character(message):
    user_id = str(message.from_user.id)

    if user_id not in characters:
        bot.reply_to(message, "У тебя нет персонажа! /create")
        return

    character = characters[user_id]
    text = f"""
Твой персонаж:

Имя: {character['name']}
Возраст: {character['age']}
Занятие: {character['job']}

Изменить: /edit
Удалить: /delete
    """

    bot.reply_to(message, text)


# Редактирование персонажа
@bot.message_handler(commands=['edit'])
def edit_character(message):
    user_id = str(message.from_user.id)

    if user_id not in characters:
        bot.reply_to(message, "У тебя нет персонажа! /create")
        return

    character = characters[user_id]

    text = f"""
Редактирование персонажа {character['name']}

Что изменить?
1. Имя
2. Возраст  
3. Занятие

Напиши цифру (1, 2 или 3)
    """

    msg = bot.reply_to(message, text)
    bot.register_next_step_handler(msg, process_edit)


def process_edit(message):
    user_id = str(message.from_user.id)
    choice = message.text.strip()

    if choice == "1":
        msg = bot.reply_to(message, "Напиши новое имя:")
        bot.register_next_step_handler(msg, edit_name)
    elif choice == "2":
        msg = bot.reply_to(message, "Напиши новый возраст:")
        bot.register_next_step_handler(msg, edit_age)
    elif choice == "3":
        msg = bot.reply_to(message, "Напиши новое занятие:")
        bot.register_next_step_handler(msg, edit_job)
    else:
        bot.reply_to(message, "Напиши цифру от 1 до 3")


def edit_name(message):
    user_id = str(message.from_user.id)
    new_name = message.text.strip()

    characters[user_id]["name"] = new_name
    save_data(JSON_FILE, characters)

    bot.reply_to(message, f"Имя изменено на '{new_name}'")


def edit_age(message):
    user_id = str(message.from_user.id)
    new_age = message.text.strip()

    characters[user_id]["age"] = new_age
    save_data(JSON_FILE, characters)

    bot.reply_to(message, f"Возраст изменен на {new_age} лет")


def edit_job(message):
    user_id = str(message.from_user.id)
    new_job = message.text.strip()

    characters[user_id]["job"] = new_job
    save_data(JSON_FILE, characters)

    bot.reply_to(message, f"Занятие изменено на '{new_job}'")


# Удаление персонажа
@bot.message_handler(commands=['delete'])
def delete_character(message):
    user_id = str(message.from_user.id)

    if user_id not in characters:
        bot.reply_to(message, "У тебя нет персонажа! /create")
        return

    name = characters[user_id]["name"]
    del characters[user_id]
    save_data(JSON_FILE, characters)

    bot.reply_to(message, f"Персонаж '{name}' удален!\nСоздать нового: /create")


# Обработка всех сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = str(message.from_user.id)
    user_message = message.text.strip()

    # Если это команда - пропускаем
    if user_message.startswith('/'):
        return

    # Получаем данные персонажа если есть
    character_data = characters.get(user_id)

    # Получаем ответ от ИИ
    ai_response = get_ai_response(user_message, character_data)

    # Сохраняем в историю
    if user_id not in chat_history:
        chat_history[user_id] = []

    chat_history[user_id].append({
        "user": user_message,
        "ai": ai_response
    })

    # Сохраняем историю
    save_data(CHAT_FILE, chat_history)

    # Отправляем ответ
    bot.reply_to(message, ai_response)


# Запуск бота
print("Бот запущен!")
print(f"Загружено персонажей: {len(characters)}")
bot.infinity_polling()