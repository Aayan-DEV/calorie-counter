# Generated by Django 5.2.1 on 2025-06-10 00:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trackgrams', '0007_auto_20250610_0017'),
    ]

    operations = [
        migrations.RenameField(
            model_name='foodentry',
            old_name='fat',
            new_name='sugar',
        ),
    ]
