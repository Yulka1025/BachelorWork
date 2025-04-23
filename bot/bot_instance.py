from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

API_TOKEN = "7330837211:AAEyUOJjqdrBWDUq5MvMw-cZxUil1Cz8hpk"

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
