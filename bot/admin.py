from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import *


@admin.register(PizzaList)
class PizzaListAdmin(ModelAdmin):
    list_display = ('title', 'price', 'description')
    list_filter = ('title', 'price')
    search_fields = ('title',)


@admin.register(DrinkList)
class DrinkListAdmin(ModelAdmin):
    list_display = ('title', 'price', 'description')
    list_filter = ('title', 'price')
    search_fields = ('title',)


@admin.register(SauceList)
class SauceListAdmin(ModelAdmin):
    list_display = ('title', 'price', 'description')
    list_filter = ('title', 'price')
    search_fields = ('title',)