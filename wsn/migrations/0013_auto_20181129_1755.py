# Generated by Django 2.1.2 on 2018-11-29 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wsn', '0012_auto_20181118_0805'),
    ]

    operations = [
        migrations.AlterField(
            model_name='frame',
            name='time',
            field=models.IntegerField(editable=False, null=True),
        ),
    ]
