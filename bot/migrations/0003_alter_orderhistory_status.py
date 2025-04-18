# Generated by Django 5.1.4 on 2025-03-21 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0002_cart_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderhistory',
            name='status',
            field=models.CharField(choices=[('new', 'Новий'), ('pending', 'Очікує підтвердження'), ('preparing', 'Готується'), ('shipped', 'В дорозі'), ('completed', 'Завершено'), ('canceled', 'Скасовано')], default='pending', max_length=20, verbose_name='Статус'),
        ),
    ]
