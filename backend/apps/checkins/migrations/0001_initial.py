# Generated manually for the shared study room system.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyCheckIn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('checkin_date', models.DateField(verbose_name='打卡日期')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_checkins', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '每日打卡',
                'verbose_name_plural': '每日打卡',
                'ordering': ['-checkin_date', '-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='dailycheckin',
            constraint=models.UniqueConstraint(fields=('user', 'checkin_date'), name='unique_user_checkin_date'),
        ),
    ]
