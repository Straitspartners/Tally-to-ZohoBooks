# Generated by Django 5.1.2 on 2025-05-23 10:41

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0015_rename_phone_ledger_ledger_mobile_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Vendor",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("parent", models.CharField(blank=True, max_length=255, null=True)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("address", models.TextField(blank=True, null=True)),
                (
                    "ledger_mobile",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                ("website", models.URLField(blank=True, null=True)),
                ("state_name", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "country_name",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("pincode", models.CharField(blank=True, max_length=10, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("user", "name")},
            },
        ),
    ]
