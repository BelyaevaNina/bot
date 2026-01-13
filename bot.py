import random
import time
import requests
import json
from telethon import TelegramClient, events
import atexit

api_id = 33100781
api_hash = "851e421911ca88d83e20e276c953453c"
phone = "+79897939606"
BOT_TOKEN = "8275700528:AAECybc5-QPbiXS4ZO9NmJ_-Hapk_GnexI0"
CHAT_ID = -1001183977989
BOT_USERNAME = "retransforgamebot"

OLLAMA_URL = "http://localhost:11434/api/generate"
SEND_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

VOID_API_KEY = "sk-voidai-Io4dDslOL7WKyFsYZk5gYR15AjIcCZ4XU0wjPImO1ke-i5cSjdctY5US9Y5JILhaRwk8QpE_HuRmXqIHUMiRDLecpru1kx9t-Ehiqhsoj_5iNZKGvXKX4zd8131wDYftE6OZnQ"
VOID_API_URL = "https://api.voidai.app/v1/chat/completions"
VOID_MODEL = "gpt-5.1"  # пример, поменяешь если надо

client = TelegramClient("boychat", api_id, api_hash)

# ---------------- ПАМЯТЬ --------------------------
chat_history = []
MAX_HISTORY = 10

# ---------------- АНТИ-ФЛУД -----------------------
LAST_REPLY_TIME = 0
MIN_REPLY_DELAY = 3.0   # сек между ответами

# Инициализация переменной current_prompt
current_prompt = "Ты милая няшка стесняшка. Максимум 3 предложения"
# ---------------- LLM: QWEN3 1.7B ---------------------
def ask_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {VOID_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": VOID_MODEL,  # Используем новую модель gpt-5.2-chat-latest
        "messages": [
            {"role": "system", "content": "Привет бот"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.9,  # Сделаем более творческий ответ
        "max_tokens": 500,    # Увеличиваем количество токенов
        "top_p": 0.9,         # Лучшая вероятность интересных ответов
        "n": 1                # Количество вариантов ответа
    }

    try:
        # Отправка запроса
        response = requests.post(VOID_API_URL, json=data, headers=headers, timeout=40)

        # Логирование полного ответа
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")

        if response.status_code == 200:
            response_json = response.json()
            content = response_json["choices"][0]["message"]["content"].strip()
            if not content:
                return "я пизда тупая добавь мне токены 😭"
            return content
        else:
            print(f"Ошибка от VoidAI: {response.status_code}")
            return "Что-то пошло не так 😭"
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при подключении к VoidAI: {e}")
        return "Что-то пошло не так, подожди немного... 😭"

# ---------------- ПРОМПТ --------------------------

# ---------------- ПРОМПТ --------------------------
def build_prompt(username, text, prompt):
    history_block = "\n".join(chat_history[-MAX_HISTORY:])
    return f"""{prompt}

Не говори что ты бот или ИИ.

Вот история чата:
{history_block}

Новое сообщение от @{username}: "{text}"

Ответь от первого лица.
"""

# ---------------- ТРИГГЕРЫ ------------------------

TRIGGERS_CALL = [
    "@retransforgamebot", "бот", "ботик", "эй", "помоги", "вопрос", "Вопрос"
]

TRIGGERS_EMO = [
    "бля", "пиздец", 
    "устал", "устала", "плохо", "груст", "тяжко",
    "капец", "не понимаю", "непон", 
    "смешно", 
]

def should_reply(username, text):
    txt = text.lower()

    if username == BOT_USERNAME.lower():
        return False

    if any(t in txt for t in TRIGGERS_CALL):
        return True

    if any(t in txt for t in TRIGGERS_EMO):
        return True

    if random.random() < 0.1:
        return True

    return False

# ---------------- SEND ----------------------------

def send_message(text):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
        "chat_id": CHAT_ID,
        "text": text
    })

# ---------------- TELETHON -------------------------

@client.on(events.NewMessage(chats=CHAT_ID))
async def handler(event):
    global LAST_REPLY_TIME, current_prompt, chat_history

    sender = await event.get_sender()
    username = (sender.username or "").lower()
    text = event.raw_text or ""

    print(f"\n>>> @{username}: {text}")

    # Обработка команды /help
    if text == "/help@retransforgamebot":
        send_message("Привет долбаеб! Спроси меня что угодно, отзываюсь на @retransforgamebot, 'бот', 'ботик', 'эй', 'помоги'")
        return

# Проверяем, если сообщение соответствует формату /setprompt @retransforgamebot <текст>
    if text.startswith("/setprompt@retransforgamebot"):
        command_parts = text.split(" ", 1)
        if len(command_parts) > 1 and command_parts[1].strip():  # Проверяем, если текст после команды не пустой
            current_prompt = command_parts[1].strip()  # Устанавливаем новый промт
            chat_history = []  # Очищаем историю чата при изменении промта
            send_message(f"Промт успешно обновлен на: {current_prompt}")
        else:
            send_message("Текст для промта не может быть пустым!")
        return

    # Сброс промта
    elif text == "/resetprompt@retransforgamebot":
        current_prompt = "Ты — максимально отбитый, матерый зек при этом романтичный бандит."
        chat_history = []  # Очищаем историю чата при сбросе промта
        send_message("Промт сброшен к исходному состоянию.")
        return

    # Показать текущий промт
    elif text == "/showprompt@retransforgamebot":
        send_message(f"Текущий промт: {current_prompt}")
        return

     # Проверка на "томат" в разных регистрах
    if "томат" in text.lower() and username != BOT_USERNAME.lower():  # Поиск по слову "томат" (не зависит от регистра)
        print("Томат найден, бот отвечает...")
        send_message("Томат лучший <3")
        return  # Выход из обработчика, чтобы не выполнять дальнейшую обработку
    
    if "сглып" in text.lower() and username != BOT_USERNAME.lower():  # Поиск по слову "томат" (не зависит от регистра)
            print("Сглыпа найден, бот отвечает...")
            send_message("Сглыпа хуесос")
            return  # Выход из обработчика, чтобы не выполнять дальнейшую обработку


    # сохраняем в память
    chat_history.append(f"{username}: {text}")
    if len(chat_history) > MAX_HISTORY:
        chat_history.pop(0)

    # анти-флуд
    now = time.time()
    if now - LAST_REPLY_TIME < MIN_REPLY_DELAY:
        print("анти-флуд: пропуск")
        return

    # фильтр реакции
    if not should_reply(username, text):
        print("бот решил промолчать")
        return

    print("бот отвечает...")

    prompt = build_prompt(username, text, current_prompt)  # Передаем актуальный промт в build_prompt
    answer = ask_llm(prompt)

    print("<<< BOT:", answer)

    send_message(answer)
    LAST_REPLY_TIME = time.time()

# ---------------- TEST ----------------------------

# Запускаем тест для проверки правильности работы API
def test_ask_llm():
    prompt = "Привет, как дела?"
    response = ask_llm(prompt)
    print(f"Тестовый ответ: {response}")

# Тестируем работу API
test_ask_llm()  # Тестируем работу API

# ---------------- START ---------------------------
client.start(phone=phone)
print(f"⚡ {VOID_MODEL} чат-тян запущена — отвечает быстро и по делу.")
client.run_until_disconnected()
