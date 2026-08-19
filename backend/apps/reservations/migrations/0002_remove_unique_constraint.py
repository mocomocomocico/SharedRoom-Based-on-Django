from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='reservation',
            name='unique_seat_date_slot_status',
        ),
    ]
