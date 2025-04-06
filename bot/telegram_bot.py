import asyncio
import logging

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery,
)
from asgiref.sync import sync_to_async

from bot.checkout import router  # ✅ Імпортуємо router
from .menu import *
from .models import *

API_TOKEN = "7330837211:AAEyUOJjqdrBWDUq5MvMw-cZxUil1Cz8hpk"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)

dp = Dispatcher()

dp.include_router(router)

keyboard_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Меню🍽"), KeyboardButton(text="Допомога у виборі🌐")],
        [KeyboardButton(text="Про нас👥"), KeyboardButton(text="Доставка🚘")],
        [KeyboardButton(text="Корзина🛒"), KeyboardButton(text="Замовлення📜")],
    ],
    resize_keyboard=True,
)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    photo_path = "/Users/tareekov/Desktop/BachelorWork/media/drinks/sticker_1.jpg"
    photo = FSInputFile(photo_path)  # Використання FSInputFile для локального файлу
    await message.answer_photo(
        photo=photo,
        caption="Привіт! Радий бачити тебе в одній з "
        "найкращих піцерій Луцька. Гайда в меню та роби замовлення!",
        reply_markup=keyboard_main,
    )

    await BotUser.objects.aget_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )


menu_list = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Напої🥤", callback_data="drinks")],
        [InlineKeyboardButton(text="Піцца🍕", callback_data="pizza")],
        [InlineKeyboardButton(text="Соус🫙", callback_data="sauce")],
    ]
)


@dp.message(lambda message: message.text == "Меню🍽")
async def menu_all(message: Message):
    photo_path = "/Users/tareekov/Desktop/BachelorWork/media/drinks/sticker_1.jpg"
    photo = FSInputFile(photo_path)
    await message.answer_photo(
        photo=photo,
        caption="Обирай що саме сьогодні припаде тобі до душі",
        reply_markup=menu_list,
    )


django.setup()


@dp.callback_query(F.data == "pizza")
async def send_pizza(callback: CallbackQuery):
    logger.info("Отримання піци")
    keyboard = await get_menu_for_category(PizzaList, "pizza")  # Отримуємо меню піци
    logger.info(f"Меню піци отримано: {keyboard}")
    await callback.message.answer("Оберіть піцу з меню:", reply_markup=keyboard)

    @dp.callback_query(F.data.startswith("pizza_item_"))
    async def process_pizza_callback(callback_query: CallbackQuery):
        await send_item_details(callback_query, PizzaList, "pizza")


@dp.callback_query(F.data == "drinks")
async def send_drinks(callback: CallbackQuery):
    logger.info("Отримання напоїв")
    keyboard = await get_menu_for_category(DrinkList, "drink")  # Отримуємо меню напоїв
    logger.info(f"Меню напоїв отримано: {keyboard}")
    await callback.message.answer("Оберіть напій з меню:", reply_markup=keyboard)

    @dp.callback_query(F.data.startswith("drink_item_"))
    async def process_drink_callback(callback_query: CallbackQuery):
        await send_item_details(callback_query, DrinkList, "drink")


@dp.callback_query(F.data == "sauce")
async def send_sauces(callback: CallbackQuery):
    logger.info("Отримання соусів")
    keyboard = await get_menu_for_category(SauceList, "sauce")  # Отримуємо меню соусів
    logger.info(f"Меню соусів отримано: {keyboard}")
    await callback.message.answer("Оберіть соус з меню:", reply_markup=keyboard)

    @dp.callback_query(F.data.startswith("sauce_item_"))
    async def process_sauce_callback(callback_query: CallbackQuery):
        await send_item_details(callback_query, SauceList, "sauce")


async def send_item_details(callback_query: CallbackQuery, model_class, item_type: str):
    try:
        # Отримуємо ID елемента
        logger.debug(f"Отримано callback_data: {callback_query.data}")
        logger.debug(f"item_type: {item_type}")

        data_parts = callback_query.data.split("_")
        if item_type not in ["pizza", "drink", "sauce"]:
            logger.error(f"Некоректний item_type: {item_type}")
            await callback_query.answer(
                "Невідома категорія. Спробуйте ще раз.", show_alert=True
            )
            return

        if len(data_parts) < 3:
            await callback_query.answer(
                "Невірний формат даних. Спробуйте ще раз.", show_alert=True
            )
            return

        item_id = int(data_parts[2])
        item = await sync_to_async(model_class.objects.get)(
            id=item_id
        )  # Отримуємо об'єкт товару

        # Початкова кількість товару
        quantity = 1

        # Перевіряємо наявність інформації про кошик у callback_data
        if "|" in callback_query.data:
            cart_total = callback_query.data.split("|")[1]  # Загальна сума кошика
        else:
            cart_total = "0"

        # Текст повідомлення
        text = (
            f"**{item.title}**\n\n"
            f"{item.description}\n\n"
            f"💵 Ціна: {item.price} грн\n"
        )

        # Inline-кнопки
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌", callback_data=f"remove_{item_type}_{item_id}"
                    ),
                    InlineKeyboardButton(
                        text="➖", callback_data=f"decrease_{item_type}_{item_id}"
                    ),
                    InlineKeyboardButton(
                        text="➕", callback_data=f"increase_{item_type}_{item_id}"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=f"✅ Додати {quantity} шт. - {item.price * quantity} грн",
                        callback_data=f"add_to_cart_{item_type}_{item_id}_{quantity}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="<< Назад", callback_data=f"back_to_menu_{item_type}"
                    ),
                    InlineKeyboardButton(
                        text=f"<< Кошик ({cart_total} грн)", callback_data="view_cart"
                    ),
                ],
            ]
        )

        # Якщо є фото
        if item.photo and item.photo.path:
            photo = FSInputFile(item.photo.path)
            await callback_query.message.bot.send_photo(
                chat_id=callback_query.message.chat.id,
                photo=photo,
                caption=text,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
        else:
            await callback_query.message.answer(
                text, parse_mode="Markdown", reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"Помилка у send_item_details: {e}")
        await callback_query.answer(
            "Сталася помилка. Спробуйте ще раз пізніше.", show_alert=True
        )


@sync_to_async
def get_or_create_cart(telegram_id):
    """Отримуємо або створюємо кошик без прив'язки до користувача."""
    user = BotUser.objects.filter(telegram_id=telegram_id).first()
    cart = Cart.objects.filter(is_active=True, user=user).last()
    if not cart:
        cart = Cart.objects.create(is_active=True, user=user)
    return cart


@dp.callback_query(lambda callback: callback.data.startswith("increase_"))
async def handle_increase(callback_query: types.CallbackQuery, state):
    cart = await get_or_create_cart(callback_query.from_user.id)

    await handle_callback(
        callback_query,
        state,
        cart=cart,
        model_classes={"pizza": PizzaList, "drink": DrinkList, "sauce": SauceList},
    )


@dp.callback_query(lambda callback: callback.data.startswith("decrease_"))
async def handle_decrease(callback_query: CallbackQuery, state):
    cart = await get_or_create_cart(callback_query.from_user.id)

    await handle_callback(
        callback_query,
        state,
        cart=cart,
        model_classes={"pizza": PizzaList, "drink": DrinkList, "sauce": SauceList},
    )


@sync_to_async
def update_cart_total(cart_id):
    try:
        cart, created = Cart.objects.get_or_create(
            id=cart_id, defaults={"total_sum": 0}
        )
    except Exception as e:
        logger.error(f"❌ Помилка при отриманні кошика: {e}")
        return

    cart_items = CartItem.objects.filter(cart=cart)
    cart.total_sum = sum(item.price * item.quantity for item in cart_items)
    cart.save()


@dp.callback_query(lambda callback: callback.data.startswith("add_to_cart_"))
async def handle_add_to_cart(callback_query: CallbackQuery, state):
    try:
        data_parts = callback_query.data.split("_")
        item_type = data_parts[3]
        item_id = int(data_parts[4])

        # ⬇️ Отримуємо кількість із `state`, а не callback_data!
        state_data = await state.get_data()
        current_quantity = state_data.get(
            f"{item_type}_{item_id}_quantity", 1
        )  # Якщо немає - ставимо 1

        model_classes = {
            "pizza": PizzaList,
            "drink": DrinkList,
            "sauce": SauceList,
        }

        model_class = model_classes.get(item_type)
        if not model_class:
            await callback_query.answer("Невідомий тип товару.", show_alert=True)
            return

        # Отримуємо товар (асинхронно)
        item = await sync_to_async(lambda: model_class.objects.get(id=item_id))()

        # Отримуємо/створюємо кошик
        cart = await get_or_create_cart(callback_query.from_user.id)

        # Додаємо/оновлюємо товар у кошику
        cart_item, created = await sync_to_async(
            lambda: CartItem.objects.get_or_create(
                category=item_type,
                item_id=item_id,
                cart=cart,
                defaults={
                    "title": item.title,
                    "price": item.price,
                    "quantity": current_quantity,
                },
            )
        )()

        if not created:
            cart_item.quantity += current_quantity
            await cart_item.asave()

        # Додаємо товар у кошик
        await sync_to_async(cart.items.add)(cart_item)

        # 🔹 ГАРАНТОВАНО ОНОВЛЮЄМО ЗАГАЛЬНУ СУМУ КОШИКА
        await update_cart_total(cart.id)

        # 🔹 ЧЕКАЄМО, ПОКИ ДАНІ ОНОВЛЯТЬСЯ В БД
        await asyncio.sleep(0.1)  # ⏳ Даємо час базі оновитися

        # 🔹 ОТРИМУЄМО АКТУАЛЬНЕ ЗНАЧЕННЯ СУМИ
        cart = await sync_to_async(lambda: Cart.objects.get(id=cart.id))()
        cart_total = cart.total_sum  # Тепер значення коректне

        # 🔹 ОНОВЛЮЄМО КНОПКУ "КОШИК"
        keyboard = callback_query.message.reply_markup.inline_keyboard
        new_cart_text = (
            f"<< Кошик ({cart_total} грн)" if cart_total > 0 else "<< Кошик (0 грн)"
        )

        for row in keyboard:
            for button in row:
                if "<< Кошик" in button.text:
                    button.text = new_cart_text  # Оновлюємо текст кнопки
                    break
        updated_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        # 🔹 ОНОВЛЮЄМО КЛАВІАТУРУ
        await callback_query.message.edit_reply_markup(reply_markup=updated_markup)

        # 🔹 ВІДПРАВЛЯЄМО ПІДТВЕРДЖЕННЯ КОРИСТУВАЧУ
        await callback_query.answer(
            f"✅ {item.title} ({current_quantity} шт.) додано до кошика! Загальна сума: {cart_total} грн.",
            show_alert=True,
        )

    except Exception as e:
        logger.error(f"Помилка у handle_add_to_cart: {e}")
        await callback_query.answer(
            "❌ Помилка при додаванні в кошик!", show_alert=True
        )


# handle_callback функція з логікою збільшення, зменшення, видалення товару тощо


async def handle_callback(callback_query: CallbackQuery, state, cart, model_classes):
    try:
        # Парсинг callback_data
        data_parts = callback_query.data.split("_")

        action = data_parts[0]  # increase, decrease, add_to_cart, back_to_menu, remove
        item_type = data_parts[1]  # pizza, drink, sauce
        item_id = int(data_parts[2])  # ID товару

        # Витягуємо потрібний клас моделі та об'єкт
        model_class = model_classes.get(item_type)
        if not model_class:
            await callback_query.answer("Невідома категорія товару.", show_alert=True)
            return

        item = await sync_to_async(model_class.objects.get)(id=item_id)

        # Отримуємо поточну кількість товару зі стану
        state_data = await state.get_data()
        current_quantity = state_data.get(
            f"{item_type}_{item_id}_quantity", 1
        )  # Значення за замовчуванням: 1

        # Логіка дій
        if action == "increase":
            current_quantity += 1
            await update_cart_total(cart.id)  # Оновлюємо суму кошика
            cart_total = await sync_to_async(
                lambda: cart.total_sum
            )()  # Отримуємо нову суму
        elif action == "decrease" and current_quantity > 1:
            current_quantity -= 1
            await update_cart_total(cart.id)  # Оновлюємо суму кошика
            cart_total = await sync_to_async(
                lambda: cart.total_sum
            )()  # Отримуємо нову суму
        elif action == "add_to_cart":
            await sync_to_async(cart.add_item)(
                category=item_type,
                item_id=item_id,
                title=item.title,
                price=item.price,
                quantity=current_quantity,
            )
            await update_cart_total(cart.id)  # Оновлюємо загальну суму кошика
            cart_total = await sync_to_async(
                lambda: cart.total_sum
            )()  # Отримуємо нову суму

            await callback_query.message.answer(f"✅ {item.title} додано до кошика!")
            return
        elif action == "remove":
            current_quantity = 1
            await update_cart_total(cart.id)  # Оновлюємо суму кошика
            cart_total = await sync_to_async(
                lambda: cart.total_sum
            )()  # Отримуємо нову суму
        elif action == "back_to_menu":
            await callback_query.message.edit_text("⬅️ Повернення до меню...")
            return await send_item_details(callback_query, model_class, item_type)

        # Оновлення стану
        await state.update_data({f"{item_type}_{item_id}_quantity": current_quantity})

        # Формуємо текст повідомлення
        text = (
            f"**{item.title}**\n\n"
            f"{item.description}\n\n"
            f"💵 Ціна: {item.price} грн\n"
        )

        # Перевіряємо наявність інформації про кошик
        cart_total = await sync_to_async(lambda: cart.total_sum)()

        # Формуємо кнопки
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌", callback_data=f"remove_{item_type}_{item_id}"
                    ),
                    InlineKeyboardButton(
                        text="➖", callback_data=f"decrease_{item_type}_{item_id}"
                    ),
                    InlineKeyboardButton(
                        text="➕", callback_data=f"increase_{item_type}_{item_id}"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=f"✅ Додати {current_quantity} шт. - {item.price * current_quantity} грн",
                        callback_data=f"add_to_cart_{item_type}_{item_id}_{current_quantity}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="<< Назад", callback_data=f"back_to_menu_{item_type}"
                    ),
                    InlineKeyboardButton(
                        text=f"<< Кошик ({cart_total} грн)", callback_data="view_cart"
                    ),
                ],
            ]
        )

        # Оновлюємо повідомлення

        if callback_query.message.photo:
            await callback_query.message.edit_caption(
                caption=text, parse_mode="Markdown", reply_markup=keyboard
            )
        else:
            await callback_query.message.edit_text(
                text, parse_mode="Markdown", reply_markup=keyboard
            )

    except Exception as e:
        # Логування помилки
        logger.error(f"Помилка у handle_callback: {e}")
        await callback_query.answer(
            "Сталася помилка. Спробуйте ще раз пізніше.", show_alert=True
        )


@dp.callback_query(lambda callback: callback.data.startswith("back_to_menu_"))
async def back_to_menu(callback_query: CallbackQuery):
    try:
        data_parts = callback_query.data.split("_")

        item_type = data_parts[3]

        logger.debug(f"Отримано callback_data: {callback_query.data}")
        logger.debug(f"item_type: {item_type}")

        # Вибираємо відповідну функцію для відображення меню
        if item_type == "pizza":
            await send_pizza(callback_query)
        elif item_type == "drink":
            await send_drinks(callback_query)
        elif item_type == "sauce":
            await send_sauces(callback_query)
        else:
            await callback_query.answer(
                f"Невідома категорія. Спробуйте ще раз. {item_type}", show_alert=True
            )
            return

        cart = await Cart.objects.aget(
            user__telegram_id=callback_query.from_user.id, is_active=True
        )
        cart_total = cart.total_sum

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"<< Кошик ({cart_total} грн)", callback_data="view_cart"
                    ),
                ],
            ]
        )

    except Exception as e:
        logger.error(f"Помилка у handle_back_to_menu: {e}")
        await callback_query.answer(
            "Сталася помилка. Спробуйте ще раз пізніше.", show_alert=True
        )


async def get_item_price(item_type: str, item_id: int) -> int:
    """Отримує ціну товару з БД, використовуючи sync_to_async"""
    model_map = {"pizza": PizzaList, "drink": DrinkList, "sauce": SauceList}

    model = model_map.get(item_type)
    if not model:
        return 0

    try:
        item = await sync_to_async(model.objects.get)(
            id=item_id
        )  # Виконуємо ORM-запит у окремому потоці
        return item.price
    except model.DoesNotExist:
        return 0


@dp.callback_query(F.data.startswith("remove_"))
async def reset_quantity(callback: CallbackQuery, state):
    try:
        _, item_type, item_id = callback.data.split("_")
        item_id = int(item_id)

        # Скидаємо кількість до 1 у state
        await state.update_data({f"{item_type}_{item_id}_quantity": 1})

        # Отримуємо актуальну ціну з БД
        item_price = await get_item_price(item_type, item_id)

        if not callback.message.reply_markup:
            await callback.answer("❌ Помилка: немає клавіатури!")
            return

        # Оновлюємо текст кнопки
        keyboard = callback.message.reply_markup.inline_keyboard
        for row in keyboard:
            for button in row:
                if button.callback_data.startswith(
                    f"add_to_cart_{item_type}_{item_id}"
                ):
                    button.text = f"✅ Додати 1 шт. - {item_price} грн"
                    break

        updated_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        # Оновлюємо повідомлення
        await callback.message.edit_reply_markup(reply_markup=updated_markup)
        await callback.answer("✅ Кількість скинута до 1!")

    except Exception as e:
        logger.error(f"Помилка у reset_quantity: {e}")
        await callback.answer("❌ Помилка при скиданні кількості!", show_alert=True)


async def get_cart_items(telegram_id):
    cart = await Cart.objects.filter(user__telegram_id=telegram_id).alast()
    items = await sync_to_async(list)(CartItem.objects.filter(cart=cart).all())
    return {
        str(item.id): {
            "name": item.title,
            "quantity": item.quantity,
            "price": item.price,
            "category": item.category,
            "item_id": item.item_id,
        }
        for item in items
    }


def generate_cart_keyboard(cart_items, cart_total):
    keyboard_buttons = []

    for item_id, item in cart_items.items():
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{item['name']} - {item['quantity']} шт. {item['price']} грн",
                    callback_data=f"item_{item_id}",
                )
            ]
        )

        # ✅ Отримуємо category та item_id правильно
        category = item.get("category", "unknown")
        item_id = item.get("item_id", item_id)  # Тепер беремо item_id з CartItem

        # ✅ Створюємо правильний callback_data
        callback_data_edit = f"edit_{category}_{item_id}"
        callback_data_delete = f"delete_{category}_{item_id}"
        print(callback_data_edit, callback_data_delete)

        logger.debug(
            f"✅ Згенеровано callback_data для редагування: {callback_data_edit}"
        )
        logger.debug(
            f"🔍 Генерація callback_data: category={category}, item_id={item_id}"
        )

        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="Змінити ✏", callback_data=callback_data_edit
                ),
                InlineKeyboardButton(
                    text="Видалити ⛔", callback_data=callback_data_delete
                ),
            ]
        )

    if keyboard_buttons:
        keyboard_buttons.append(
            [InlineKeyboardButton(text="🗑 Оформити", callback_data="checkout")]
        )
        keyboard_buttons.append(
            [InlineKeyboardButton(text="🚫 Відмінити", callback_data="cancel")]
        )
        return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


async def show_cart(message, user_id):
    cart_items = await get_cart_items(user_id)
    cart_total = (
        sum(item["price"] * item["quantity"] for item in cart_items.values())
        if cart_items
        else 0
    )
    print(cart_total, cart_items)
    keyboard = generate_cart_keyboard(cart_items, cart_total)
    text = (
        f"🛒 Ваше замовлення:\n_Загальна сума: {cart_total} грн_"
        if cart_items
        else "🛒 Ваш кошик порожній."
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@dp.callback_query(lambda c: c.data == "view_cart")
async def show_cart_callback(callback_query: CallbackQuery):
    await show_cart(callback_query.message, callback_query.from_user.id)

    await callback_query.answer()


@dp.message(F.text == "Корзина🛒")
async def show_cart_message(message: Message):
    await show_cart(message, message.from_user.id)


@dp.callback_query(lambda c: c.data.startswith("edit_"))
async def edit_item(callback_query: CallbackQuery):
    parts = callback_query.data.split("_")

    # Якщо parts містить лише 3 елементи (edit, category, item_id), додаємо "view"
    if len(parts) == 3:
        parts.insert(1, "view")  # Додаємо "view" як дію за замовчуванням

    if len(parts) < 4:
        logger.error(f"❌ Некоректний callback_data: {callback_query.data}")
        await callback_query.answer("❌ Помилка: некоректні дані.", show_alert=True)
        return

    _, action, category, item_id_str = parts
    item_id = int(item_id_str)

    cart = await Cart.objects.filter(
        user__telegram_id=callback_query.from_user.id
    ).alast()

    cart_item = await sync_to_async(
        lambda: CartItem.objects.filter(
            category=category, item_id=item_id, cart=cart
        ).last()
    )()
    if not cart_item:
        await callback_query.answer("❌ Товар не знайдено у кошику.", show_alert=True)
        return

    if action == "increase":
        cart_item.quantity += 1
    elif action == "decrease" and cart_item.quantity > 1:
        cart_item.quantity -= 1
    elif action == "confirm":
        await show_cart_callback(callback_query)
        return

    await cart_item.asave()
    cart_total = await sync_to_async(
        lambda: sum(
            item.price * item.quantity
            for item in CartItem.objects.filter(cart=cart).all()
        )
    )()
    await update_cart_total(cart_total)

    new_text = f"**{cart_item.title}**\n\n💵 Ціна: {cart_item.price} грн\n📦 Кількість: {cart_item.quantity} шт."

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➖", callback_data=f"edit_decrease_{category}_{item_id}"
                ),
                InlineKeyboardButton(
                    text="➕", callback_data=f"edit_increase_{category}_{item_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"✅ Зберегти",
                    callback_data=f"edit_confirm_{category}_{item_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"<< Кошик ({cart_total} грн)", callback_data="view_cart"
                )
            ],
        ]
    )

    current_text = callback_query.message.text
    current_markup = callback_query.message.reply_markup

    if current_text != new_text or current_markup != keyboard:
        await callback_query.message.edit_text(
            new_text, reply_markup=keyboard, parse_mode="Markdown"
        )
    else:
        await callback_query.answer("ℹ Немає змін у замовленні.", show_alert=False)

    await callback_query.answer()


@dp.callback_query(lambda c: c.data.startswith(("edit_increase_", "edit_decrease_")))
async def change_quantity(callback_query: CallbackQuery):
    parts = callback_query.data.split("_")  # Розбиваємо `callback_data`

    if len(parts) != 4:  # Перевіряємо коректність розміру
        logger.error(f"❌ Некоректний callback_data: {callback_query.data}")
        await callback_query.answer("❌ Помилка: некоректні дані.", show_alert=True)
        return

    edit_prefix, action, category, item_id_str = parts  # Виправлений розподіл змінних
    item_id = int(item_id_str)
    cart = await Cart.objects.filter(
        user__telegram_id=callback_query.from_user.id
    ).alast()
    cart_item = await sync_to_async(
        lambda: CartItem.objects.filter(
            category=category, item_id=item_id, cart=cart
        ).alast()
    )()
    if not cart_item:
        await callback_query.answer("❌ Товар не знайдено у кошику.", show_alert=True)
        return

    if action == "increase":
        cart_item.quantity += 1
    elif action == "decrease" and cart_item.quantity > 1:
        cart_item.quantity -= 1

    await sync_to_async(cart_item.save)()
    await update_cart_total(cart_item.carts.first().id)

    await edit_item(callback_query)


@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def delete_item(callback_query: CallbackQuery):
    parts = callback_query.data.split("_")

    if len(parts) != 3:  # Очікуємо формат delete_category_itemID
        logger.error(f"❌ Некоректний callback_data: {callback_query.data}")
        await callback_query.answer("❌ Помилка: некоректні дані.", show_alert=True)
        return

    _, category, item_id_str = parts
    item_id = int(item_id_str)
    cart = await Cart.objects.filter(
        user__telegram_id=callback_query.from_user.id
    ).alast()
    # Видаляємо товар із кошика
    await sync_to_async(
        lambda: CartItem.objects.filter(
            category=category, item_id=item_id, cart=cart
        ).delete()
    )()

    # Оновлюємо загальну суму кошика
    cart_total = await sync_to_async(
        lambda: sum(
            item.price * item.quantity
            for item in CartItem.objects.filter(cart=cart).all()
        )
    )()
    await update_cart_total(cart_total)

    # Показуємо оновлену корзину
    await show_cart_callback(callback_query)


@dp.message(F.text == "Замовлення📜")
async def show_orders(message: Message):
    user = await BotUser.objects.aget(telegram_id=message.from_user.id)
    orders = await sync_to_async(list)(OrderHistory.objects.filter(user=user))
    if not orders:
        await message.answer("У вас немає замовлень.")
        return

    text = "Ваші замовлення:\n\n"
    for order in orders:
        text += (
            f"Замовлення #{order.id}:\n"
            f"Сума: {order.total_sum} грн\n"
            f"Статус: {order.get_status_display()}\n"
            f"Дата: {order.created_at}\n\n"
        )

    await message.answer(text)


async def main():
    print("Бот запущений...")
    await dp.start_polling(bot, handle_signals=False)


if __name__ == "__main__":
    asyncio.run(main())
