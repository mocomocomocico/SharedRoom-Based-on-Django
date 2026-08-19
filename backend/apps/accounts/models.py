# 用户模块模型：扩展 Django User 的资料字段，并保存信用分/违规记录。
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    credit_score = models.IntegerField(default=100, verbose_name='信用分')
    violation_count = models.PositiveIntegerField(default=0, verbose_name='违规次数')

    def __str__(self):
        return self.user.username


class ViolationRecord(models.Model):
    TYPE_NO_SHOW = 'no_show'
    TYPE_MANUAL = 'manual'
    TYPE_OTHER = 'other'
    TYPE_CHOICES = [
        (TYPE_NO_SHOW, '未签到爽约'),
        (TYPE_MANUAL, '管理员记录'),
        (TYPE_OTHER, '其他违规'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='violation_records')
    reservation = models.ForeignKey('reservations.Reservation', on_delete=models.SET_NULL, null=True, blank=True, related_name='violation_records')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_violation_records')
    violation_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_OTHER)
    reason = models.CharField(max_length=255)
    score_delta = models.IntegerField(default=-10, verbose_name='信用分变动')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        verbose_name = '违规记录'
        verbose_name_plural = '违规记录'

    def __str__(self):
        return f"{self.user.username}-{self.violation_type}-{self.score_delta}"
