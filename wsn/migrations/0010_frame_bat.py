# Generated by Django 2.1.2 on 2018-11-14 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wsn', '0009_auto_20181111_1203'),
    ]

    operations = [
        migrations.AddField(
            model_name='frame',
            name='bat',
            field=models.SmallIntegerField(editable=False, null=True),
        ),
    ]