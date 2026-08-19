from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0004_free_time_reservation'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='credit_score',
            field=models.IntegerField(default=100, verbose_name='信用分'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='violation_count',
            field=models.PositiveIntegerField(default=0, verbose_name='违规次数'),
        ),
        migrations.CreateModel(
            name='ViolationRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('violation_type', models.CharField(choices=[('no_show', '未签到爽约'), ('manual', '管理员记录'), ('other', '其他违规')], default='other', max_length=20)),
                ('reason', models.CharField(max_length=255)),
                ('score_delta', models.IntegerField(default=-10, verbose_name='信用分变动')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_violation_records', to=settings.AUTH_USER_MODEL)),
                ('reservation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='violation_records', to='reservations.reservation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='violation_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at', '-id'],
                'verbose_name': '违规记录',
                'verbose_name_plural': '违规记录',
            },
        ),
    ]
