# 座位模型：维护座位基础信息和可预约时间段。
from django.db import models


class Seat(models.Model):
    TYPE_NORMAL = 'normal'
    TYPE_QUIET = 'quiet'
    TYPE_WINDOW = 'window'
    TYPE_POWER = 'power'
    TYPE_CHOICES = [
        (TYPE_NORMAL, '普通位'),
        (TYPE_QUIET, '安静位'),
        (TYPE_WINDOW, '靠窗位'),
        (TYPE_POWER, '插座位'),
    ]

    seat_code = models.CharField(max_length=50, unique=True, verbose_name='座位编号')
    area = models.CharField(max_length=50, blank=True, verbose_name='区域')
    is_active = models.BooleanField(default=True, verbose_name='可用状态')
    note = models.CharField(max_length=200, blank=True, verbose_name='备注')
    map_row = models.PositiveIntegerField(default=1, verbose_name='平面图行')
    map_col = models.PositiveIntegerField(default=1, verbose_name='平面图列')
    seat_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_NORMAL, verbose_name='座位类型')
    has_power = models.BooleanField(default=False, verbose_name='是否带插座')
    near_window = models.BooleanField(default=False, verbose_name='是否靠窗')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['map_row', 'map_col', 'seat_code']
        verbose_name = '座位'
        verbose_name_plural = '座位'

    def __str__(self):
        return self.seat_code


class TimeSlot(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='时段名称')
    start_time = models.TimeField(verbose_name='开始时间')
    end_time = models.TimeField(verbose_name='结束时间')
    is_active = models.BooleanField(default=True, verbose_name='可用状态')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'start_time']
        verbose_name = '时段'
        verbose_name_plural = '时段'

    def __str__(self):
        return self.name
