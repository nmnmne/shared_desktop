# Generated by Django 4.2.11 on 2024-08-05 13:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0005_saveconfigfiles_saveconflictstxt_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="saveconfigfiles",
            options={
                "verbose_name": "SaveConfigFiles",
                "verbose_name_plural": "SaveConfigFiles",
            },
        ),
        migrations.AlterModelOptions(
            name="saveconflictstxt",
            options={
                "verbose_name": "SaveConflictsTXT",
                "verbose_name_plural": "SaveConflictsTXT",
            },
        ),
        migrations.AlterField(
            model_name="saveconfigfiles",
            name="file",
            field=models.FileField(null=True, upload_to="conflicts/configs/"),
        ),
        migrations.AlterField(
            model_name="saveconflictstxt",
            name="file",
            field=models.FileField(null=True, upload_to="conflicts/txt/"),
        ),
    ]
