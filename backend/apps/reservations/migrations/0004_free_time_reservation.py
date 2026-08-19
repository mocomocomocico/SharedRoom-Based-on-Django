import datetime


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0003_seed_demo_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='time_slot',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reservations', to='seats.timeslot'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='start_time',
            field=models.TimeField(default=datetime.time(8, 0), verbose_name='开始时间'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reservation',
            name='end_time',
            field=models.TimeField(default=datetime.time(9, 0), verbose_name='结束时间'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reservation',
            name='checkin_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='reservation',
            name='checkout_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='status',
            field=models.CharField(choices=[('booked', '已预约'), ('checked_in', '已签到'), ('completed', '已签退'), ('cancelled', '已取消'), ('expired', '已过期')], default='booked', max_length=20),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='cancelled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
