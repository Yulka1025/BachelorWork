from django.contrib.auth.models import AbstractUser
from django.db import models


class PizzaList(models.Model):
    title = models.CharField(max_length=255, verbose_name="Назва піцци")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    description = models.CharField(
        max_length=255, verbose_name="Опис", default="Опис відсутній"
    )
    photo = models.ImageField(upload_to="pizzas/", null=True, blank=True)

    class Meta:
        verbose_name = "Піцца"
        verbose_name_plural = "Піцци"

    def __str__(self):
        return f"{self.title} - {self.price} грн"


class DrinkList(models.Model):
    title = models.CharField(max_length=255, verbose_name="Напій")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    description = models.CharField(
        max_length=255, verbose_name="Опис", default="Опис відсутній"
    )
    photo = models.ImageField(upload_to="drinks/", null=True, blank=True)

    class Meta:
        verbose_name = "Напій"
        verbose_name_plural = "Напої"

    def __str__(self):
        return f"{self.title} - {self.price} грн"


class SauceList(models.Model):
    title = models.CharField(max_length=255, verbose_name="Соус")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    description = models.CharField(
        max_length=255, verbose_name="Опис", default="Опис відсутній"
    )
    photo = models.ImageField(upload_to="sauces/", null=True, blank=True)

    class Meta:
        verbose_name = "Соус"
        verbose_name_plural = "Соуси"

    def __str__(self):
        return f"{self.title} - {self.price} грн"


class CartItem(models.Model):
    CATEGORY_CHOICES = [
        ("pizza", "Піца"),
        ("drink", "Напій"),
        ("sauce", "Соус"),
    ]

    cart = models.ForeignKey(
        "bot.Cart",
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="Корзина",
    )
    category = models.CharField(
        max_length=10, choices=CATEGORY_CHOICES, verbose_name="Категорія"
    )
    item_id = models.PositiveIntegerField(verbose_name="ID товару")
    title = models.CharField(max_length=255, verbose_name="Назва")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Кількість")

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.title} x {self.quantity}"


class BotUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    first_name = models.CharField(
        max_length=255, verbose_name="Ім'я", null=True, blank=True
    )
    last_name = models.CharField(
        max_length=255, verbose_name="Прізвище", null=True, blank=True
    )
    username = models.CharField(
        max_length=255, verbose_name="Юзернейм", null=True, blank=True
    )

    class Meta:
        verbose_name = "Користувач"
        verbose_name_plural = "Користувачі"

    def __str__(self):
        return self.first_name


class DeliveryData(models.Model):
    user = models.ForeignKey(
        BotUser,
        on_delete=models.CASCADE,
        related_name="delivery_data",
        verbose_name="Користувач",
    )
    address = models.CharField(
        max_length=255, verbose_name="Адреса", blank=True, null=True
    )
    name = models.CharField(max_length=255, verbose_name="Iм'я")
    phone_number = models.CharField(
        max_length=15, verbose_name="Номер телефону", blank=True, null=True
    )

    class Meta:
        verbose_name = "Дані для доставки"
        verbose_name_plural = "Дані для доставки"


class Cart(models.Model):
    user = models.ForeignKey(
        BotUser,
        on_delete=models.CASCADE,
        related_name="carts",
        verbose_name="Користувач",
        null=True,  # Дозволяємо значення NULL
        blank=True,
    )
    items = models.ManyToManyField(
        CartItem, related_name="carts", verbose_name="Товари"
    )
    total_sum = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Корзина #{self.id} (Сума: {self.total_sum} грн)"


class OrderHistory(models.Model):
    STATUS_CHOICES = [
        ("paid for", "Оплачено"),
        ("new", "Новий"),
        ("pending", "Очікує підтвердження"),
        ("preparing", "Готується"),
        ("shipped", "В дорозі"),
        ("completed", "Завершено"),
        ("canceled", "Скасовано"),
    ]
    PAYMENT_METHODS = [
        ("cash", "Готівка"),
        ("card", "Карта"),
        ("online", "Онлайн оплата"),
    ]
    user = models.ForeignKey(
        BotUser,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Користувач",
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        verbose_name="Спосіб оплати",
        default="cash",
    )
    items = models.ManyToManyField(
        CartItem, related_name="order_histories", verbose_name="Товари"
    )
    total_sum = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Загальна сума"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="new", verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    class Meta:
        verbose_name = "Історія замовлень"
        verbose_name_plural = "Історія замовлень"

    def __str__(self):
        return f"Замовлення #{self.id} (Користувач: {self.user.first_name}, Сума: {self.total_sum} грн)"
