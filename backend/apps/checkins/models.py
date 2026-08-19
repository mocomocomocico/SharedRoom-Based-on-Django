# 每日打卡模型：记录用户每天是否完成学习打卡。
from django.conf import settings
from django.db import models


class DailyCheckIn(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_checkins')
    checkin_date = models.DateField(verbose_name='打卡日期')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-checkin_date', '-created_at']
        verbose_name = '每日打卡'
        verbose_name_plural = '每日打卡'
        constraints = [
            models.UniqueConstraint(fields=['user', 'checkin_date'], name='unique_user_checkin_date'),
        ]

    def __str__(self):
        return f'{self.user.username}-{self.checkin_date}'
