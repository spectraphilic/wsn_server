# Generated by Django 2.1.2 on 2018-11-10 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wsn', '0006_frame_process_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='frame',
            name='pulse_CNR4_Tot',
            field=models.SmallIntegerField(editable=False, null=True),
        ),
    ]