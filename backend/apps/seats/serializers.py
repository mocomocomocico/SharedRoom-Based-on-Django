# 座位序列化器：把座位基础字段与指定日期下的可预约状态一起返回给前端。
from rest_framework import serializers

from .models import Seat, TimeSlot
from apps.reservations.models import Reservation
from apps.reservations.time_utils import build_free_time_ranges, MIN_BOOKABLE_MINUTES


class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ('id', 'name', 'start_time', 'end_time', 'is_active', 'sort_order')


class SeatSerializer(serializers.ModelSerializer):
    is_booked = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    remaining_count = serializers.SerializerMethodField()
    remaining_minutes = serializers.SerializerMethodField()
    next_available_range = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    seat_type_label = serializers.SerializerMethodField()

    class Meta:
        model = Seat
        fields = (
            'id', 'seat_code', 'area', 'is_active', 'note',
            'map_row', 'map_col', 'seat_type', 'seat_type_label', 'has_power', 'near_window',
            'is_booked', 'status_label', 'remaining_count', 'remaining_minutes', 'next_available_range', 'is_full',
        )

    def _bookable_ranges(self, obj):
        # 根据当前查询日期和已占用预约，计算还能预约的时间段。
        reservation_date = self.context.get('reservation_date')
        if not reservation_date:
            return None
        qs = Reservation.objects.filter(
            seat=obj,
            reservation_date=reservation_date,
            status__in=[Reservation.STATUS_BOOKED, Reservation.STATUS_CHECKED_IN],
        ).order_by('start_time')
        occupied = [(item.get_start_datetime(), item.get_end_datetime()) for item in qs]
        free_ranges = build_free_time_ranges(reservation_date, occupied)
        return [item for item in free_ranges if int((item[1] - item[0]).total_seconds() // 60) >= MIN_BOOKABLE_MINUTES]

    def get_is_booked(self, obj):
        if not obj.is_active:
            return True
        ranges = self._bookable_ranges(obj)
        if ranges is None:
            return False
        return len(ranges) == 0

    def get_status_label(self, obj):
        if not obj.is_active:
            return '不可用'
        if self._bookable_ranges(obj) is None:
            return '可用'
        return '已约满' if self.get_is_booked(obj) else '可预约'

    def get_remaining_count(self, obj):
        ranges = self._bookable_ranges(obj)
        return len(ranges) if ranges is not None else 0

    def get_remaining_minutes(self, obj):
        ranges = self._bookable_ranges(obj)
        if not ranges:
            return 0
        total = 0
        for start_dt, end_dt in ranges:
            total += int((end_dt - start_dt).total_seconds() // 60)
        return total

    def get_next_available_range(self, obj):
        ranges = self._bookable_ranges(obj)
        if not ranges:
            return None
        start_dt, end_dt = ranges[0]
        return {
            'start_time': start_dt.strftime('%H:%M'),
            'end_time': end_dt.strftime('%H:%M'),
            'label': f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}",
            'duration_minutes': int((end_dt - start_dt).total_seconds() // 60),
        }

    def get_is_full(self, obj):
        return self.get_remaining_minutes(obj) < MIN_BOOKABLE_MINUTES if obj.is_active else True

    def get_seat_type_label(self, obj):
        return dict(Seat.TYPE_CHOICES).get(obj.seat_type, obj.seat_type)



class SeatCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = (
            'id', 'seat_code', 'area', 'is_active', 'note',
            'map_row', 'map_col', 'seat_type', 'has_power', 'near_window',
        )

    def validate_map_row(self, value):
        # 平面图坐标至少从 1 开始，避免前端 grid 出现无效位置。
        return max(1, value)

    def validate_map_col(self, value):
        # 平面图坐标至少从 1 开始，避免前端 grid 出现无效位置。
        return max(1, value)
