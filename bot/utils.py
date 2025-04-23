from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from django.conf import settings
from .models import *


def get_order_admin_url(order_id: int) -> str:
    return f"https://your-site.com/admin/bot/orderhistory/{order_id}/change/"


async def send_new_order_notification(bot: Bot, order_id: int, ordername: str, total_sum: float):
    url = get_order_admin_url(order_id)
    text = (
        f"🆕 <b>Нове замовлення #{order_id}</b>\n"
        f"👤 Клієнт: {ordername}\n"
        f"💰 Сума: {total_sum:.2f} грн"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Переглянути в адмінці", url=url)]
    ])

    await bot.send_message(
        chat_id=settings.TELEGRAM_ADMIN_CHAT_ID,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
