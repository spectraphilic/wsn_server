# Generated by Django 2.0.4 on 2018-05-11 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wsn', '0002_auto_20180419_0913'),
    ]

    operations = [
        migrations.AddField(
            model_name='frame',
            name='METNORA_99_99_1_1_1',
            field=models.FloatField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='frame',
            name='METNORR_99_99_1_1_1',
            field=models.FloatField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='frame',
            name='P_RAIN_8_19_1_1_1',
            field=models.FloatField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='frame',
            name='SR50DISTANCE_9_99_1_1_1',
            field=models.FloatField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='frame',
            name='SR50QUALITY_99_99_1_1_1',
            field=models.FloatField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='frame',
            name='shf_cal_1',
            field=models.FloatField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='frame',
            name='shf_cal_2',
            field=models.FloatField(editable=False, null=True),
        ),
    ]