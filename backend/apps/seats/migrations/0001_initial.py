from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Seat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seat_code', models.CharField(max_length=50, unique=True, verbose_name='座位编号')),
                ('area', models.CharField(blank=True, max_length=50, verbose_name='区域')),
                ('is_active', models.BooleanField(default=True, verbose_name='可用状态')),
                ('note', models.CharField(blank=True, max_length=200, verbose_name='备注')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['seat_code'], 'verbose_name': '座位', 'verbose_name_plural': '座位'},
        ),
        migrations.CreateModel(
            name='TimeSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='时段名称')),
                ('start_time', models.TimeField(verbose_name='开始时间')),
                ('end_time', models.TimeField(verbose_name='结束时间')),
                ('is_active', models.BooleanField(default=True, verbose_name='可用状态')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='排序')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['sort_order', 'start_time'], 'verbose_name': '时段', 'verbose_name_plural': '时段'},
        ),
    ]
