# Generated by Django 3.2.16 on 2024-06-26 17:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['created_at'], 'verbose_name': 'комментарий', 'verbose_name_plural': 'Комментарии'},
        ),
    ]