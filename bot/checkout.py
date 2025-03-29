import django
import os

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
from bot.models import BotUser, OrderHistory  # Імпортуй свої моделі!

router = Router()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bachelor.settings")  # ✅ Вказуємо Django settings
django.setup()  # ✅ Ініціалізуємо Django

# 📌 Машина станів (FSM)
class CheckoutStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_address = State()
    waiting_for_payment = State()
    waiting_for_phone = State()


# 🟢 1. Натискання "Оформити"
@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Ваше ім'я:")
    await state.set_state(CheckoutStates.waiting_for_name)


# 🟢 2. Отримуємо ім'я
@router.message(CheckoutStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Адреса доставки:")
    await state.set_state(CheckoutStates.waiting_for_address)


# 🟢 3. Отримуємо адресу
@router.message(CheckoutStates.waiting_for_address)
async def get_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Готівка")], [KeyboardButton(text="Карта")], [KeyboardButton(text="Онлайн")]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("Оберіть спосіб оплати:", reply_markup=keyboard)
    await state.set_state(CheckoutStates.waiting_for_payment)


# 🟢 4. Отримуємо оплату
@router.message(CheckoutStates.waiting_for_payment)
async def get_payment(message: Message, state: FSMContext):
    await state.update_data(payment=message.text)

    if message.text.lower() == "онлайн":
        data = await state.get_data()
        name = data.get("name")
        address = data.get("address")

        # Замість get_or_create за name → шукаємо за Telegram ID:
        telegram_id = message.from_user.id
        print("📲 TELEGRAM USER ID:", message.from_user.id)
        user, created = await sync_to_async(BotUser.objects.get_or_create)(
            telegram_id=telegram_id,
            defaults={"name": name, "address": address}
        )
        print("👤 BotUser ID:", user.id)
        print("🆕 Було створено нового користувача?", created)

        # Шукаємо активну корзину
        from bot.models import Cart  # 👈 Імпорт тут, бо Django.setup() уже працює
        cart = await Cart.objects.filter(id=telegram_id, is_active=True).order_by("-created_at").afirst()

        if cart:
            print(f"🛒 Cart знайдено: ID={cart.id}, Сума: {cart.total_sum}")
            print(f"📦 Привʼязана до користувача ID: {cart.user.telegram_id}")
        else:
            print("🚫 Cart НЕ знайдено для user.id:", user.telegram_id)

        if not cart or not await sync_to_async(cart.items.exists)():
            await message.answer("Ваша корзина порожня 🍕")
            await state.clear()
            return

        total_sum = float(cart.total_sum)

        # Створюємо замовлення
        order = await sync_to_async(OrderHistory.objects.create)(
            user=user,
            total_sum=total_sum,
            status="new",
            payment_method="online"
        )
        await sync_to_async(order.items.set)(cart.items.all())

        # Генеруємо посилання LiqPay
        liqpay_url = generate_liqpay_url(
            amount=total_sum,
            order_id=f"order_{order.id}_bot",
            description=f"Оплата замовлення #{order.id}"
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="💳 Сплатити через LiqPay", url=liqpay_url)]]
        )

        await message.answer(
            f"✅ Замовлення #{order.id} оформлено!\n"
            f"*Ім’я:* {name}\n"
            f"*Адреса:* {address}\n"
            f"*Сума:* {total_sum} грн\n"
            f"*Оплата:* Онлайн",
            parse_mode="Markdown",
            reply_markup=kb
        )

        # Деактивуємо корзину після оформлення
        cart.is_active = False
        await sync_to_async(cart.save)()

        await state.clear()

    else:
        # Якщо НЕ онлайн — переходимо до запиту номера телефону
        contact_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Поділитися контактом", request_contact=True)]],
            resize_keyboard=True, one_time_keyboard=True
        )
        await message.answer("Надішліть номер телефону або поділіться контактом:", reply_markup=contact_keyboard)
        await state.set_state(CheckoutStates.waiting_for_phone)


# 🟢 5. Отримуємо телефон і зберігаємо у БД
@router.message(CheckoutStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone_number=phone)

    # ✅ Отримуємо всі дані
    data = await state.get_data()
    name, address, payment = data["name"], data["address"], data["payment"]

    # ✅ Створюємо або отримуємо користувача
    user, created = await sync_to_async(BotUser.objects.get_or_create)(
        name=name, telegram_id=message.from_user.id, defaults={"address": address, "phone_number": phone}
    )

    # ✅ Створюємо замовлення
    order = await sync_to_async(OrderHistory.objects.create)(
        user=user, total_sum=0, status="pending", payment_method=payment
    )

    # ✅ Відповідь користувачу
    await message.answer(
        f"✅ Замовлення оформлено!\n\n"
        f"*Iм’я:* {name}\n"
        f"*Адреса:* {address}\n"
        f"*Оплата:* {payment}\n"
        f"*Телефон:* {phone}\n"
        f"*Номер замовлення:* {order.id}",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )

    await state.clear()


import base64
import hashlib
import json

PUBLIC_KEY = 'sandbox_i76181583427'
PRIVATE_KEY = 'sandbox_QGnb2EkKBPAZGed3LU9ApBGnhBFa5i3ID0YpGIzy'

CALLBACK_URL = 'https://example.com/liqpay-callback/'  # Тимчасово


def generate_liqpay_url(amount: int, order_id: str, description: str = "Оплата"):
    data = {
        "public_key": PUBLIC_KEY,
        "version": "3",
        "action": "pay",
        "amount": str(amount),
        "currency": "UAH",
        "description": description,
        "order_id": order_id,
        "server_url": CALLBACK_URL,
    }

    json_data = json.dumps(data)
    encoded_data = base64.b64encode(json_data.encode()).decode()
    sign_string = PRIVATE_KEY + encoded_data + PRIVATE_KEY
    signature = base64.b64encode(hashlib.sha1(sign_string.encode()).digest()).decode()

    url = f"https://www.liqpay.ua/api/3/checkout?data={encoded_data}&signature={signature}"
    return url
