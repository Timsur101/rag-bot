import os
import telebot
from dotenv import load_dotenv
from rag import add_document, ask

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# храним документы пользователей в памяти (для простоты)
user_docs = {}


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id,
        "Привет! Я помогу отвечать на вопросы по твоим документам.\n\n"
        "Команды:\n"
        "/upload - загрузить текст\n"
        "/ask - задать вопрос\n"
        "/clear - очистить документы"
    )


@bot.message_handler(commands=["upload"])
def upload(message):
    bot.send_message(message.chat.id, "Отправь текст который хочешь загрузить:")
    bot.register_next_step_handler(message, save_document)


def save_document(message):
    user_id = str(message.chat.id)
    text = message.text

    if not text:
        bot.send_message(message.chat.id, "Текст пустой, попробуй снова")
        return

    add_document(user_id, text)
    bot.send_message(message.chat.id, "Документ загружен! Теперь можешь задавать вопросы через /ask")


@bot.message_handler(commands=["ask"])
def ask_question(message):
    bot.send_message(message.chat.id, "Задай свой вопрос:")
    bot.register_next_step_handler(message, answer_question)


def answer_question(message):
    user_id = str(message.chat.id)
    question = message.text

    bot.send_message(message.chat.id, "Ищу ответ...")

    answer = ask(user_id, question)
    bot.send_message(message.chat.id, answer)


@bot.message_handler(commands=["clear"])
def clear(message):
    user_id = str(message.chat.id)
    # очищаем индекс пользователя
    from rag import clear_user
    clear_user(user_id)
    bot.send_message(message.chat.id, "Документы очищены")


if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling()
