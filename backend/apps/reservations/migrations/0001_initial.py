from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('seats', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reservation_date', models.DateField(verbose_name='预约日期')),
                ('status', models.CharField(choices=[('booked', '已预约'), ('cancelled', '已取消')], default='booked', max_length=20)),
                ('note', models.CharField(blank=True, max_length=200)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('seat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='seats.seat')),
                ('time_slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='seats.timeslot')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='auth.user')),
            ],
            options={
                'verbose_name': '预约记录',
                'verbose_name_plural': '预约记录',
                'ordering': ['-reservation_date', 'time_slot__start_time', '-created_at'],
                'constraints': [
                    models.UniqueConstraint(fields=('seat', 'reservation_date', 'time_slot', 'status'), name='unique_seat_date_slot_status'),
                ],
            },
        ),
    ]
