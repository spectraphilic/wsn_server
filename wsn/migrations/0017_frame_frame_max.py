# Generated by Django 2.1.5 on 2019-02-26 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wsn', '0016_auto_20181205_1215'),
    ]

    operations = [
        migrations.AddField(
            model_name='frame',
            name='frame_max',
            field=models.SmallIntegerField(editable=False, null=True),
        ),
    ]