# Generated by Django 3.2.5 on 2021-09-02 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wsn', '0022_auto_20210902_1101'),
    ]

    operations = [
        migrations.AlterField(
            model_name='frame',
            name='data',
            field=models.JSONField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='tags',
            field=models.JSONField(editable=False, null=True),
        ),
    ]
