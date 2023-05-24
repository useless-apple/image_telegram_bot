import os
import random
from datetime import datetime

import telebot
from PIL import Image, ImageDraw, ImageFont
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

TG_TOKEN = os.environ['TG_TOKEN']
IMAGE_DIR = os.environ['IMAGE_DIR']
TEXT_FILE = os.environ['TEXT_FILE']
FONT_FILE = os.environ['FONT_FILE']
REPOST_CHANNEL_ID = os.environ['REPOST_CHANNEL_ID']

bot = telebot.TeleBot(TG_TOKEN)


def gen_markup() -> object:
    """
    Добавляет кнопки под картинкой
    :return: markup
    """
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Отправить фото", callback_data="share"))
    markup.add(InlineKeyboardButton("Удалить фото", callback_data="delete"))
    return markup


def get_random_text(text_file: str = TEXT_FILE) -> str:
    """
    Получает рандомный текст из файла
    :param text_file: Путь до файла с текстом
    :return: Случайную фразу
    """
    text_list = [i.strip() for i in open(text_file).readlines()]
    return random.choice(text_list)


def write_text_to_photo(filepath: str, text: str) -> None:
    """
    Накладывает текст на изображение
    :param filepath: Путь до фотографии
    :param text: Накладываемый текст
    :return: None
    """
    image = Image.open(filepath)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_FILE, size=25, encoding="utf-8")
    width_image, height_image = image.size
    width_text, height_text = draw.textsize(text, font=font)

    width_global = width_image - width_text
    draw.text(
        (width_global / 2 + 1, ((height_image / 10) * 9) + 1),
        text,
        font=font,
        fill=(0, 0, 0, 0)
    )
    draw.text(
        (width_global / 2, ((height_image / 10) * 9)),
        text,
        font=font,
        fill=(255, 255, 255, 1)
    )
    image.save(filepath)


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, """\
                        Возникли проблемы?
                        Перезагрузи меня!\
                        """)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """\
                        Привет, я Бесполезный бот.
                        Отправь мне картинку, и я верну тебе картинку с текстом!\
                        """)


@bot.message_handler(commands=['text'])
def send_text(message):
    bot.reply_to(message, """\
                        Я тебя не понимаю.
                        Отправь мне картинку, и я верну тебе картинку с текстом!\
                        """)


@bot.message_handler(content_types=['photo'])
def image(message) -> None:
    bot_message = bot.reply_to(message, "Загружаю изобаржение")

    file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
    file_downloaded = bot.download_file(file_info.file_path)

    image_type = file_info.file_path.split('.')[-1]

    image_name = "{}_{}.{}".format(datetime.now().strftime("%Y-%m-%d_%H_%M"), message.from_user.id, image_type)
    image_path = "{}/{}".format(IMAGE_DIR, image_name)
    if not os.path.exists(IMAGE_DIR):
        os.mkdir(IMAGE_DIR)
    with open(image_path, 'wb') as file_new:
        file_new.write(file_downloaded)

    bot.edit_message_text(chat_id=bot_message.chat.id, message_id=bot_message.id, text='Обрабатываю изображение')
    text = get_random_text()
    write_text_to_photo(image_path, text)

    with open(image_path, 'rb') as f:
        bot.send_photo(message.chat.id, f, reply_markup=gen_markup())

    bot.delete_message(chat_id=bot_message.chat.id, message_id=bot_message.id)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call) -> None:
    if call.data == "share":
        bot.answer_callback_query(call.id, "Отправил!")
        bot.forward_message(REPOST_CHANNEL_ID, call.from_user.id, call.message.message_id)
    if call.data == "delete":
        bot.answer_callback_query(call.id, "Изображение удалено!")
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)


bot.polling()
