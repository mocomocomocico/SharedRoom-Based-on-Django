# 预约模型：记录用户、座位、日期、自由开始/结束时间和预约状态。

from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.seats.models import Seat, TimeSlot


class Reservation(models.Model):
    STATUS_BOOKED = 'booked'
    STATUS_CHECKED_IN = 'checked_in'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_EXPIRED = 'expired'
    STATUS_CHOICES = [
        (STATUS_BOOKED, '已预约'),
        (STATUS_CHECKED_IN, '已签到'),
        (STATUS_COMPLETED, '已签退'),
        (STATUS_CANCELLED, '已取消'),
        (STATUS_EXPIRED, '已过期'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateField(verbose_name='预约日期')
    start_time = models.TimeField(verbose_name='开始时间')
    end_time = models.TimeField(verbose_name='结束时间')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_BOOKED)
    note = models.CharField(max_length=200, blank=True)
    checkin_at = models.DateTimeField(null=True, blank=True)
    checkout_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-reservation_date', 'start_time', '-created_at']
        verbose_name = '预约记录'
        verbose_name_plural = '预约记录'

    def get_start_datetime(self):
        tz = timezone.get_current_timezone()
        return timezone.make_aware(datetime.combine(self.reservation_date, self.start_time), tz)

    def get_end_datetime(self):
        tz = timezone.get_current_timezone()
        return timezone.make_aware(datetime.combine(self.reservation_date, self.end_time), tz)

    def get_checkin_deadline(self):
        return self.get_start_datetime() + timedelta(minutes=15)

    def __str__(self):
        return f'{self.user.username}-{self.seat.seat_code}-{self.reservation_date}-{self.start_time}-{self.end_time}-{self.status}'
