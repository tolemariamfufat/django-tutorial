# Generated by Django 5.1 on 2024-08-27 07:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("formsapp", "0007_alter_venue_owner"),
    ]

    operations = [
        migrations.AddField(
            model_name="venue",
            name="Venue_image",
            field=models.ImageField(blank=True, null=True, upload_to="images/"),
        ),
    ]
