from django.db import migrations, models

def fix_foodentry_data(apps, schema_editor):
    FoodEntry = apps.get_model('trackgrams', 'FoodEntry')
    # The 'grams' field currently contains calorie data due to the wrong rename
    # We need to fix this by moving the data back to calories and setting proper grams
    for entry in FoodEntry.objects.all():
        # The current 'grams' field actually contains calories
        actual_calories = entry.grams  # This is actually calories due to wrong migration
        entry.calories = actual_calories
        entry.grams = 100  # Set a default grams value
        entry.save()

def reverse_fix_foodentry_data(apps, schema_editor):
    pass  # We don't want to reverse this fix

class Migration(migrations.Migration):
    dependencies = [
        ('trackgrams', '0006_alter_foodentry_options_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_foodentry_data, reverse_fix_foodentry_data),
    ]