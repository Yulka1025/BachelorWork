from django.contrib import admin
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin, StackedInline
from unfold.decorators import display

from .models import *


class OrderHistoryGroupsInline(StackedInline):
    model = OrderHistory
    ordering_field = ("-created_at",)
    extra = 0


@admin.register(PizzaList)
class PizzaListAdmin(ModelAdmin):
    list_display = ("title", "price", "description")
    list_filter = ("title", "price")
    search_fields = ("title",)


@admin.register(DrinkList)
class DrinkListAdmin(ModelAdmin):
    list_display = ("title", "price", "description")
    list_filter = ("title", "price")
    search_fields = ("title",)


@admin.register(SauceList)
class SauceListAdmin(ModelAdmin):
    list_display = ("title", "price", "description")
    list_filter = ("title", "price")
    search_fields = ("title",)


@admin.register(BotUser)
class BotUserAdmin(ModelAdmin):
    list_display = ("telegram_id", "username", "first_name", "last_name")
    list_filter = ("username", "first_name", "last_name")
    search_fields = ("username", "first_name", "last_name")
    inlines = (OrderHistoryGroupsInline,)


@admin.register(DeliveryData)
class DeliveryDataAdmin(ModelAdmin):
    list_display = ("display_user", "address", "name", "phone_number")
    list_filter = ("address", "name", "phone_number")
    search_fields = ("address", "name", "phone_number")

    def display_user(self, obj):
        return obj.user.first_name


@admin.register(OrderHistory)
class OrderHistoryAdmin(ModelAdmin):
    list_display = ("user", "total_sum", "display_status", "payment_method")
    list_filter = ("status", "payment_method")
    search_fields = ("user__username", "total_sum", "status", "payment_method")

    @display(
        description="Status",
        label={
            "paid for": "success",
            "pending": "warning",
            "canceled": "danger",
            "shipped": "success",
            "in_progress": "info",
            "preparing": "info",
        },
    )
    @mark_safe
    def display_status(self, instance: OrderHistory):
        return instance.get_status_display()
