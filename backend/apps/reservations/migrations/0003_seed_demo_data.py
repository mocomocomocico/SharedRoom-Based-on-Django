
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.utils import timezone


def seed_demo_data(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('accounts', 'UserProfile')
    Seat = apps.get_model('seats', 'Seat')
    TimeSlot = apps.get_model('seats', 'TimeSlot')
    Reservation = apps.get_model('reservations', 'Reservation')

    demo_users = [
        {
            'username': 'admin',
            'password': 'admin123',
            'email': 'admin@example.com',
            'is_staff': True,
            'is_superuser': True,
            'nickname': '管理员',
            'phone': '13800000000',
        },
        {
            'username': 'student1',
            'password': '12345678',
            'email': 'student1@example.com',
            'is_staff': False,
            'is_superuser': False,
            'nickname': '张三',
            'phone': '13800000001',
        },
        {
            'username': 'student2',
            'password': '12345678',
            'email': 'student2@example.com',
            'is_staff': False,
            'is_superuser': False,
            'nickname': '李四',
            'phone': '13800000002',
        },
    ]

    users = {}
    for item in demo_users:
        user, created = User.objects.get_or_create(username=item['username'], defaults={
            'email': item['email'],
            'is_staff': item['is_staff'],
            'is_superuser': item['is_superuser'],
            'password': make_password(item['password']),
        })
        if not created:
            changed = False
            if not user.check_password(item['password']):
                user.password = make_password(item['password'])
                changed = True
            for field in ('email', 'is_staff', 'is_superuser'):
                if getattr(user, field) != item[field]:
                    setattr(user, field, item[field])
                    changed = True
            if changed:
                user.save(update_fields=['password', 'email', 'is_staff', 'is_superuser'])
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.nickname = item['nickname']
        profile.phone = item['phone']
        profile.save(update_fields=['nickname', 'phone'])
        users[item['username']] = user

    slots = [
        {'name': '上午时段', 'start_time': '08:00:00', 'end_time': '12:00:00', 'sort_order': 1},
        {'name': '下午时段', 'start_time': '13:00:00', 'end_time': '18:00:00', 'sort_order': 2},
        {'name': '晚间时段', 'start_time': '18:00:00', 'end_time': '00:00:00', 'sort_order': 3},
    ]

    slot_objs = {}
    for item in slots:
        slot, _ = TimeSlot.objects.get_or_create(
            name=item['name'],
            defaults={
                'start_time': item['start_time'],
                'end_time': item['end_time'],
                'is_active': True,
                'sort_order': item['sort_order'],
            }
        )
        slot_objs[item['name']] = slot

    seats = []
    for i in range(1, 9):
        code = f'A{i:02d}'
        seat, _ = Seat.objects.get_or_create(
            seat_code=code,
            defaults={
                'area': 'A区',
                'is_active': True,
                'note': '默认示例座位',
            }
        )
        seats.append(seat)

    today = timezone.localdate()
    now = timezone.localtime(timezone.now())

    sample_reservations = [
        {
            'user': users['student1'],
            'seat': seats[0],
            'reservation_date': today,
            'time_slot': slot_objs['晚间时段'],
            'status': 'booked',
            'note': '晚间自习',
        },
        {
            'user': users['student2'],
            'seat': seats[1],
            'reservation_date': today,
            'time_slot': slot_objs['下午时段'],
            'status': 'cancelled',
            'note': '已取消示例',
            'cancelled_at': now,
        },
        {
            'user': users['student2'],
            'seat': seats[2],
            'reservation_date': today + timedelta(days=1),
            'time_slot': slot_objs['上午时段'],
            'status': 'booked',
            'note': '第二天早读',
        },
    ]

    for item in sample_reservations:
        reservation, created = Reservation.objects.get_or_create(
            user=item['user'],
            seat=item['seat'],
            reservation_date=item['reservation_date'],
            time_slot=item['time_slot'],
            status=item['status'],
            defaults={
                'note': item.get('note', ''),
                'cancelled_at': item.get('cancelled_at'),
            }
        )
        if not created:
            updated_fields = []
            for field in ('note', 'cancelled_at'):
                if getattr(reservation, field) != item.get(field):
                    setattr(reservation, field, item.get(field))
                    updated_fields.append(field)
            if updated_fields:
                reservation.save(update_fields=updated_fields)


def reverse_seed_demo_data(apps, schema_editor):
    Reservation = apps.get_model('reservations', 'Reservation')
    Seat = apps.get_model('seats', 'Seat')
    TimeSlot = apps.get_model('seats', 'TimeSlot')
    UserProfile = apps.get_model('accounts', 'UserProfile')
    User = apps.get_model('auth', 'User')

    Reservation.objects.filter(user__username__in=['student1', 'student2']).delete()
    Seat.objects.filter(seat_code__in=[f'A{i:02d}' for i in range(1, 9)]).delete()
    TimeSlot.objects.filter(name__in=['上午时段', '下午时段', '晚间时段']).delete()
    UserProfile.objects.filter(user__username__in=['admin', 'student1', 'student2']).delete()
    User.objects.filter(username__in=['admin', 'student1', 'student2']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('seats', '0001_initial'),
        ('reservations', '0002_remove_unique_constraint'),
    ]

    operations = [
        migrations.RunPython(seed_demo_data, reverse_seed_demo_data),
    ]
