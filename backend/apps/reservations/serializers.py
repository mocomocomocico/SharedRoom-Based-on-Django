# 预约序列化器：把座位、用户、时间和状态转换成前端需要的展示字段。
from datetime import timedelta, time as time_cls

from django.utils import timezone
from rest_framework import serializers

from apps.accounts.services import ensure_profile
from apps.seats.models import Seat
from apps.seats.serializers import SeatSerializer

from .models import Reservation
from .time_utils import (
    get_reservation_start_datetime,
    get_reservation_end_datetime,
    time_ranges_overlap,
    RESERVABLE_START_TIME,
    RESERVABLE_END_TIME,
    MIN_BOOKABLE_MINUTES,
)


class ReservationSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_display_name = serializers.SerializerMethodField()
    seat_code = serializers.CharField(source='seat.seat_code', read_only=True)
    seat_area = serializers.CharField(source='seat.area', read_only=True)
    start_time = serializers.TimeField(read_only=True)
    end_time = serializers.TimeField(read_only=True)
    expected_release_time = serializers.SerializerMethodField()
    checkin_deadline = serializers.SerializerMethodField()
    duration_minutes = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = (
            'id', 'user_username', 'user_display_name', 'seat_code', 'seat_area',
            'reservation_date', 'start_time', 'end_time', 'expected_release_time', 'status', 'status_label',
            'note', 'checkin_at', 'checkout_at', 'checkin_deadline', 'duration_minutes',
            'cancelled_at', 'created_at', 'updated_at',
        )

    def get_user_display_name(self, obj):
        profile = getattr(obj.user, 'profile', None)
        nickname = getattr(profile, 'nickname', '') if profile else ''
        return nickname or obj.user.username

    def get_expected_release_time(self, obj):
        return obj.get_end_datetime().strftime('%Y-%m-%d %H:%M:%S')

    def get_checkin_deadline(self, obj):
        return obj.get_checkin_deadline().strftime('%Y-%m-%d %H:%M:%S')

    def get_duration_minutes(self, obj):
        return int((obj.get_end_datetime() - obj.get_start_datetime()).total_seconds() // 60)

    def get_status_label(self, obj):
        mapping = dict(Reservation.STATUS_CHOICES)
        return mapping.get(obj.status, obj.status)


class ReservationCreateSerializer(serializers.Serializer):
    seat_id = serializers.IntegerField()
    reservation_date = serializers.DateField()
    start_time = serializers.TimeField()
    duration_minutes = serializers.IntegerField(required=False, min_value=MIN_BOOKABLE_MINUTES)
    end_time = serializers.TimeField(required=False)
    note = serializers.CharField(required=False, allow_blank=True)

    def _build_end_time(self, start_dt, duration_minutes=None, end_time=None):
        if duration_minutes is not None:
            return start_dt + timedelta(minutes=duration_minutes)
        return get_reservation_end_datetime(self.initial_data.get('reservation_date') or start_dt.date(), end_time)

    def validate(self, attrs):
        seat = Seat.objects.filter(id=attrs['seat_id']).first()
        if not seat:
            raise serializers.ValidationError({'seat_id': '座位不存在'})
        if not seat.is_active:
            raise serializers.ValidationError({'seat_id': '该座位当前不可用'})

        start_time = attrs['start_time']
        duration_minutes = attrs.get('duration_minutes')
        end_time = attrs.get('end_time')
        if duration_minutes is None and end_time is None:
            raise serializers.ValidationError({'duration_minutes': '请选择结束时间或预约时长'})

        reservation_date = attrs['reservation_date']
        start_dt = get_reservation_start_datetime(reservation_date, start_time)
        if duration_minutes is not None:
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            attrs['end_time'] = end_dt.time().replace(second=0, microsecond=0)
        else:
            end_dt = get_reservation_end_datetime(reservation_date, end_time)
            attrs['duration_minutes'] = int((end_dt - start_dt).total_seconds() // 60)

        if end_dt <= start_dt:
            raise serializers.ValidationError({'end_time': '结束时间必须晚于开始时间'})

        now = timezone.localtime(timezone.now()).replace(second=0, microsecond=0)
        if end_dt <= now:
            raise serializers.ValidationError({'duration_minutes': '结束时间已经过去，不能预约'})
        if reservation_date == now.date() and start_dt < now:
            raise serializers.ValidationError({'start_time': '开始时间已经过去，不能预约'})
        if end_dt.date() != reservation_date:
            raise serializers.ValidationError({'duration_minutes': '预约时长不能跨天'})
        if start_dt.time() < RESERVABLE_START_TIME or end_dt.time() > RESERVABLE_END_TIME:
            raise serializers.ValidationError({'non_field_errors': f'预约时间需在 {RESERVABLE_START_TIME.strftime("%H:%M")} - {RESERVABLE_END_TIME.strftime("%H:%M")} 范围内'})
        if (end_dt - start_dt).total_seconds() // 60 < MIN_BOOKABLE_MINUTES:
            raise serializers.ValidationError({'duration_minutes': f'单次预约时长不能少于 {MIN_BOOKABLE_MINUTES} 分钟'})

        profile = ensure_profile(self.context['request'].user)
        if profile.credit_score < 60:
            raise serializers.ValidationError({'non_field_errors': '当前信用分低于 60 分，暂时无法预约座位'})

        active_statuses = [Reservation.STATUS_BOOKED, Reservation.STATUS_CHECKED_IN]
        seat_conflicts = Reservation.objects.filter(
            seat=seat,
            reservation_date=reservation_date,
            status__in=active_statuses,
        )
        for item in seat_conflicts:
            if time_ranges_overlap(start_time, end_dt.time().replace(second=0, microsecond=0), item.start_time, item.end_time):
                raise serializers.ValidationError({'non_field_errors': '该座位在所选时间段已被占用'})

        user_conflicts = Reservation.objects.filter(
            user=self.context['request'].user,
            reservation_date=reservation_date,
            status__in=active_statuses,
        )
        for item in user_conflicts:
            if time_ranges_overlap(start_time, end_dt.time().replace(second=0, microsecond=0), item.start_time, item.end_time):
                raise serializers.ValidationError({'non_field_errors': '你在该时间段已经有预约'})

        attrs['seat'] = seat
        attrs['end_time'] = end_dt.time().replace(second=0, microsecond=0)
        return attrs


class ReservationActionSerializer(serializers.Serializer):
    reservation_id = serializers.IntegerField()


class DashboardSummarySerializer(serializers.Serializer):
    study_minutes_today = serializers.IntegerField()
    checkin_done_today = serializers.BooleanField()
