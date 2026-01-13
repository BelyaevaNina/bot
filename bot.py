import random
import asyncio
import aiohttp
from telethon import TelegramClient, events

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

client = TelegramClient("boychat", api_id, api_hash, sequential_updates=True)

# ---------------- MEMORY --------------------------

chat_history = []
MAX_HISTORY = 10

current_prompt = "Ты милая няшка стесняшка. Максимум 3 предложения"

# ---------------- LLM -----------------------------

async def ask_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {VOID_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": VOID_MODEL,
        "messages": [
            {"role": "system", "content": "Привет бот"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.9,
        "max_tokens": 500,
        "top_p": 0.9,
        "n": 1
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                VOID_API_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=40)
            ) as resp:

                if resp.status != 200:
                    print("VoidAI error:", resp.status)
                    return "Что-то пошло не так 😭"

                data = await resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                return content or "я пизда тупая добавь мне токены 😭"

    except asyncio.TimeoutError:
        return "Сервер думает слишком долго 😭"
    except Exception as e:
        print("LLM error:", e)
        return "Что-то сломалось 😭"

# ---------------- PROMPT --------------------------

def build_prompt(username: str, text: str, base_prompt: str) -> str:
    history_block = "\n".join(chat_history[-MAX_HISTORY:])
    return f"""{base_prompt}

Не говори что ты бот или ИИ.

Вот история чата:
{history_block}

Новое сообщение от @{username}: "{text}"

Ответь от первого лица.
"""

# ---------------- TRIGGERS ------------------------

TRIGGERS_CALL = [
    "@retransforgamebot", "бот", "ботик", "эй", "помоги", "вопрос"
]

TRIGGERS_EMO = [
    "бля", "пиздец", "устал", "устала", "плохо",
    "груст", "тяжко", "капец", "не понимаю"
]

def should_reply(username: str, text: str) -> bool:
    txt = text.lower()

    if username == BOT_USERNAME.lower():
        return False

    if any(t in txt for t in TRIGGERS_CALL):
        return True

    if any(t in txt for t in TRIGGERS_EMO):
        return True

    return random.random() < 0.1

# ---------------- SEND ----------------------------

async def send_message_tg(text: str):
    await client.send_message(CHAT_ID, text)

# ---------------- HANDLER -------------------------

@client.on(events.NewMessage(chats=CHAT_ID))
async def handler(event):
    global current_prompt, chat_history

    sender = await event.get_sender()
    username = (sender.username or "").lower()
    text = event.raw_text or ""

    print(f"\n>>> @{username}: {text}")

    # /help
    if text == "/help@retransforgamebot":
        await send_message_tg(
            "Привет долбаеб! Спроси меня что угодно 😘"
        )
        return

    # /setprompt
    if text.startswith("/setprompt@retransforgamebot"):
        parts = text.split(" ", 1)
        if len(parts) > 1 and parts[1].strip():
            current_prompt = parts[1].strip()
            chat_history.clear()
            await send_message_tg(f"Промт обновлён:\n{current_prompt}")
        else:
            await send_message_tg("Промт не может быть пустым")
        return

    # /resetprompt
    if text == "/resetprompt@retransforgamebot":
        current_prompt = "Ты — максимально отбитый, матерый зек при этом романтичный бандит."
        chat_history.clear()
        await send_message_tg("Промт сброшен")
        return

    # /showprompt
    if text == "/showprompt@retransforgamebot":
        await send_message_tg(f"Текущий промт:\n{current_prompt}")
        return

    # томат
    if "томат" in text.lower() and username != BOT_USERNAME.lower():
        await send_message_tg("Томат лучший <3")
        return

    # memory
    chat_history.append(f"{username}: {text}")
    if len(chat_history) > MAX_HISTORY:
        chat_history.pop(0)

    if not should_reply(username, text):
        print("бот решил промолчать")
        return

    print("бот отвечает...")

    prompt = build_prompt(username, text, current_prompt)
    answer = await ask_llm(prompt)

    print("<<< BOT:", answer)

    await send_message_tg(answer)
    await asyncio.sleep(1.5)

# ---------------- START ---------------------------

async def main():
    await client.start(phone=phone)
    print(f"⚡ {VOID_MODEL} чат-тян запущена")
    await client.run_until_disconnected()

asyncio.run(main())
