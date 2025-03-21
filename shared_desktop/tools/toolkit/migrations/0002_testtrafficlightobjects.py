# Generated by Django 4.2.11 on 2024-11-04 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("toolkit", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TestTrafficLightObjects",
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
                ("number", models.IntegerField(default=0, unique=True)),
                ("description", models.CharField(max_length=255)),
                ("type_controller", models.CharField(max_length=10)),
                ("group", models.IntegerField(default=0)),
                ("ip_adress", models.CharField(max_length=14, null=True)),
                ("adress", models.TextField(blank=True)),
                ("time_create", models.DateTimeField(auto_now_add=True)),
                ("time_update", models.DateTimeField(auto_now=True)),
                ("connection", models.BooleanField(default=False)),
            ],
        ),
    ]
