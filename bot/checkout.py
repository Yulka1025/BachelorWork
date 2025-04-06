import os

import django
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    LabeledPrice,
    PreCheckoutQuery,
)
from asgiref.sync import sync_to_async

from bot.models import (
    BotUser,
    OrderHistory,
    DeliveryData,
    Cart,
)  # Імпортуй свої моделі!

router = Router()

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "bachelor.settings"
)  # ✅ Вказуємо Django settings
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
        keyboard=[
            [KeyboardButton(text="Готівка")],
            [KeyboardButton(text="Карта")],
            [KeyboardButton(text="Онлайн")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer("Оберіть спосіб оплати:", reply_markup=keyboard)
    await state.set_state(CheckoutStates.waiting_for_payment)


# 🟢 4. Отримуємо оплату
@router.message(CheckoutStates.waiting_for_payment)
async def get_payment(message: Message, state: FSMContext):
    await state.update_data(payment=message.text)
    data = await state.get_data()

    if message.successful_payment:
        name, address, payment, order_id, total_sum = (
            data["name"],
            data["address"],
            data["payment"],
            data["order_id"],
            data["total_sum"],
        )
        await message.answer(
            f"✅ Замовлення #{order_id} оформлено!\n"
            f"*Ім’я:* {name}\n"
            f"*Адреса:* {address}\n"
            f"*Сума:* {total_sum} грн\n"
            f"*Оплата:* Онлайн",
            parse_mode="Markdown",
        )

        # Переводимо замовлення в статус "оплачено"
        order = await OrderHistory.objects.filter(id=order_id).afirst()
        if order:
            order.status = "paid"
            await order.asave()

        await state.clear()

    if message.text.lower() == "онлайн":
        data = await state.get_data()
        name = data.get("name")
        address = data.get("address")

        # Замість get_or_create за name → шукаємо за Telegram ID:
        telegram_id = message.from_user.id
        print("📲 TELEGRAM USER ID:", message.from_user.id)
        user, created = await sync_to_async(BotUser.objects.get_or_create)(
            telegram_id=telegram_id, defaults={"name": name, "address": address}
        )
        print("👤 BotUser ID:", user.id)
        print("🆕 Було створено нового користувача?", created)

        # Шукаємо активну корзину
        from bot.models import Cart  # 👈 Імпорт тут, бо Django.setup() уже працює

        cart = (
            await Cart.objects.filter(user__telegram_id=telegram_id, is_active=True)
            .order_by("-created_at")
            .alast()
        )

        if cart:
            print(f"🛒 Cart знайдено: ID={cart.id}, Сума: {cart.total_sum}")
        else:
            print("🚫 Cart НЕ знайдено для user.id:", user.telegram_id)

        if not cart or not await cart.items.aexists():
            await message.answer("Ваша корзина порожня 🍕")
            await state.clear()
            return

        total_sum = float(cart.total_sum)

        # Створюємо замовлення
        order = await sync_to_async(OrderHistory.objects.create)(
            user=user, total_sum=total_sum, status="new", payment_method="online"
        )
        await state.update_data(
            {
                "order_id": order.id,
                "total_sum": total_sum,
            }
        )
        await sync_to_async(order.items.set)(cart.items.all())

        PRICE = LabeledPrice(
            label=f"Оплата замовлення #{order.id}", amount=int(total_sum) * 100
        )
        from bot.telegram_bot import bot

        await bot.send_invoice(
            message.chat.id,
            title=f"1Оплата замовлення #{order.id}",
            description=f"Оплата замовлення #{order.id}",
            provider_token="1661751239:TEST:91f0-pQ5h-f8Z4-FcOD",
            currency="uah",
            is_flexible=False,  # True если конечная цена зависит от способа доставки
            prices=[PRICE],
            start_parameter="time-machine-example",
            payload="some-invoice-payload-for-our-internal-use",
        )

        # Деактивуємо корзину після оформлення
        cart.is_active = False
        await cart.asave()

    else:
        # Якщо НЕ онлайн — переходимо до запиту номера телефону
        contact_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Поділитися контактом", request_contact=True)]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(
            "Надішліть номер телефону або поділіться контактом:",
            reply_markup=contact_keyboard,
        )
        await state.set_state(CheckoutStates.waiting_for_phone)


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    from bot.telegram_bot import bot

    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, state: FSMContext):
    # ✅ Отримуємо всі дані
    data = await state.get_data()

    name, address, payment, order_id, total_sum = (
        data["name"],
        data["address"],
        data["payment"],
        data["order_id"],
        data["total_sum"],
    )
    await message.answer(
        f"✅ Замовлення #{order_id} оформлено!\n"
        f"*Ім’я:* {name}\n"
        f"*Адреса:* {address}\n"
        f"*Сума:* {total_sum} грн\n"
        f"*Оплата:* Онлайн",
        parse_mode="Markdown",
    )

    await state.clear()


# 🟢 5. Отримуємо телефон і зберігаємо у БД
@router.message(CheckoutStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone_number=phone)

    # ✅ Отримуємо всі дані
    data = await state.get_data()
    name, address, payment = (
        data["name"],
        data["address"],
        data["payment"],
    )

    # ✅ Створюємо або отримуємо користувача
    user = await BotUser.objects.filter(telegram_id=message.from_user.id).afirst()
    if not user:
        await message.answer(
            "Вибачте, виникла помилка при оформленні замовлення. Спробуйте ще раз."
        )

    await DeliveryData.objects.acreate(
        user=user, name=name, address=address, phone_number=phone
    )

    # ✅ Створюємо замовлення
    order = await OrderHistory.objects.acreate(
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
        parse_mode="Markdown",
    )

    cart = await Cart.objects.filter(user__telegram_id=message.from_user.id).alast()
    cart.is_active = False
    await cart.asave()

    await state.clear()
