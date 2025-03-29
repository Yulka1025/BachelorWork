from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from asgiref.sync import sync_to_async
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bachelor.settings")
django.setup()


async def get_menu_for_category(model_class, category_name):
    """
    Загальна функція для отримання меню для конкретної категорії.
    :param model_class: Клас моделі для категорії (наприклад, PizzaList, DrinkList, SauceList).
    :param category_name: Назва категорії (наприклад, "pizza", "drink", "sauce").
    :return: клавіатура з кнопками для вибору елементів.
    """
    items = await sync_to_async(list)(model_class.objects.all())

    buttons = [
        [InlineKeyboardButton(text=f"{item.title} - {item.price} грн", callback_data=f"{category_name}_item_{item.id}")]
        for item in items
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
