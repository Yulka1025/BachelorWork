# Generated by Django 5.1.4 on 2025-02-07 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
