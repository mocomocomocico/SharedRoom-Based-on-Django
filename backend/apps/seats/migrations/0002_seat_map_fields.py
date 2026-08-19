from django.db import migrations, models


def seed_seat_layout(apps, schema_editor):
    Seat = apps.get_model('seats', 'Seat')
    seats = list(Seat.objects.all().order_by('seat_code', 'id'))
    for index, seat in enumerate(seats):
        row = index // 4 + 1
        col = index % 4 + 1
        seat.map_row = row
        seat.map_col = col
        seat.near_window = col in (1, 4)
        seat.has_power = col in (2, 3)
        seat.seat_type = 'window' if seat.near_window else 'power'
        seat.save(update_fields=['map_row', 'map_col', 'near_window', 'has_power', 'seat_type'])


class Migration(migrations.Migration):

    dependencies = [
        ('seats', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='seat',
            name='has_power',
            field=models.BooleanField(default=False, verbose_name='是否带插座'),
        ),
        migrations.AddField(
            model_name='seat',
            name='map_col',
            field=models.PositiveIntegerField(default=1, verbose_name='平面图列'),
        ),
        migrations.AddField(
            model_name='seat',
            name='map_row',
            field=models.PositiveIntegerField(default=1, verbose_name='平面图行'),
        ),
        migrations.AddField(
            model_name='seat',
            name='near_window',
            field=models.BooleanField(default=False, verbose_name='是否靠窗'),
        ),
        migrations.AddField(
            model_name='seat',
            name='seat_type',
            field=models.CharField(choices=[('normal', '普通位'), ('quiet', '安静位'), ('window', '靠窗位'), ('power', '插座位')], default='normal', max_length=20, verbose_name='座位类型'),
        ),
        migrations.RunPython(seed_seat_layout, migrations.RunPython.noop),
    ]
