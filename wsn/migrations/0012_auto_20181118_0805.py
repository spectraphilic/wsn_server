# Generated by Django 2.1.2 on 2018-11-18 08:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wsn', '0011_auto_20181117_0918'),
    ]

    operations = [
        migrations.RunSQL(
            'ALTER TABLE "wsn_frame" ALTER COLUMN "time" TYPE integer USING EXTRACT(epoch FROM time)'
        )
    ]
