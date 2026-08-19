# 预约接口：用户预约/取消/历史，以及管理端预约列表、状态变更和统计。
from datetime import datetime, timedelta, date
import calendar as pycalendar

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import ViolationRecord
from apps.accounts.services import ensure_profile
from apps.checkins.models import DailyCheckIn
from apps.materials.models import LearningMaterial
from apps.seats.models import Seat
from apps.seats.serializers import SeatSerializer

from .models import Reservation
from .serializers import (
    ReservationSerializer,
    ReservationCreateSerializer,
    ReservationActionSerializer,
)
from .services import expire_overdue_reservations, mark_no_show_violation
from .time_utils import build_free_time_ranges, format_range_payload, MIN_BOOKABLE_MINUTES


def _month_bounds(day):
    """返回指定日期所在自然月的起止日期。"""
    start = date(day.year, day.month, 1)
    if day.month == 12:
        end = date(day.year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(day.year, day.month + 1, 1) - timedelta(days=1)
    return start, end


def _sum_study_minutes(qs, now):
    """统计有效学习分钟数；进行中的记录用当前时间作为暂定结束时间。"""
    total = 0
    for item in qs:
        start = item.checkin_at or item.get_start_datetime()
        end = item.checkout_at or (now if item.status == Reservation.STATUS_CHECKED_IN else item.get_end_datetime())
        if end > start:
            total += int((end - start).total_seconds() // 60)
    return total


def _range_days(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def _daily_minutes_payload(qs, start_date, end_date, now, label_builder):
    """生成连续日期柱状图数据，缺失日期也补 0，保证图表稳定。"""
    totals = {day: 0 for day in _range_days(start_date, end_date)}
    for item in qs:
        day = item.reservation_date
        if day in totals:
            start = item.checkin_at or item.get_start_datetime()
            end = item.checkout_at or (now if item.status == Reservation.STATUS_CHECKED_IN else item.get_end_datetime())
            if end > start:
                totals[day] += int((end - start).total_seconds() // 60)
    return [
        {
            'date': day.isoformat(),
            'label': label_builder(day),
            'minutes': totals[day],
        }
        for day in totals
    ]


def _current_streak(checked_dates):
    streak = 0
    current = timezone.localdate()
    checked = set(checked_dates)
    while current in checked:
        streak += 1
        current -= timedelta(days=1)
    return streak


class ReservationMineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        expire_overdue_reservations()
        qs = Reservation.objects.select_related('seat', 'user__profile').filter(user=request.user)
        date_value = request.query_params.get('date')
        status_value = request.query_params.get('status')
        if date_value:
            qs = qs.filter(reservation_date=date_value)
        if status_value in dict(Reservation.STATUS_CHOICES):
            qs = qs.filter(status=status_value)
        return Response(ReservationSerializer(qs, many=True).data)


class ReservationBookView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        expire_overdue_reservations()
        serializer = ReservationCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        reservation = Reservation.objects.create(
            user=request.user,
            seat=data['seat'],
            reservation_date=data['reservation_date'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            note=data.get('note', ''),
            status=Reservation.STATUS_BOOKED,
        )
        return Response({'detail': '预约成功', 'reservation': ReservationSerializer(reservation).data}, status=status.HTTP_201_CREATED)


class ReservationCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        expire_overdue_reservations()
        serializer = ReservationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = Reservation.objects.select_related('user').filter(id=serializer.validated_data['reservation_id']).first()
        if not reservation:
            return Response({'detail': '预约不存在'}, status=status.HTTP_404_NOT_FOUND)
        if reservation.user_id != request.user.id and not request.user.is_staff and not request.user.is_superuser:
            return Response({'detail': '无权限取消此预约'}, status=status.HTTP_403_FORBIDDEN)
        if reservation.status != Reservation.STATUS_BOOKED:
            return Response({'detail': '当前状态无法取消'}, status=status.HTTP_400_BAD_REQUEST)
        reservation.status = Reservation.STATUS_CANCELLED
        reservation.cancelled_at = timezone.now()
        reservation.save(update_fields=['status', 'cancelled_at', 'updated_at'])
        return Response({'detail': '取消成功', 'reservation': ReservationSerializer(reservation).data})


class ReservationCheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        expire_overdue_reservations()
        serializer = ReservationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = Reservation.objects.select_related('user', 'seat').filter(id=serializer.validated_data['reservation_id'], user=request.user).first()
        if not reservation:
            return Response({'detail': '预约不存在'}, status=status.HTTP_404_NOT_FOUND)
        if reservation.status != Reservation.STATUS_BOOKED:
            return Response({'detail': '当前状态无法签到'}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.localtime(timezone.now())
        start_dt = reservation.get_start_datetime()
        deadline = reservation.get_checkin_deadline()
        end_dt = reservation.get_end_datetime()
        if now < start_dt:
            return Response({'detail': '未到签到时间'}, status=status.HTTP_400_BAD_REQUEST)
        if now > deadline:
            reservation.status = Reservation.STATUS_EXPIRED
            reservation.cancelled_at = reservation.cancelled_at or now
            reservation.save(update_fields=['status', 'cancelled_at', 'updated_at'])
            mark_no_show_violation(reservation, now)
            return Response({'detail': '该预约已过期，无法签到，并已记录为违规'}, status=status.HTTP_400_BAD_REQUEST)
        if now >= end_dt:
            reservation.status = Reservation.STATUS_EXPIRED
            reservation.cancelled_at = reservation.cancelled_at or now
            reservation.save(update_fields=['status', 'cancelled_at', 'updated_at'])
            mark_no_show_violation(reservation, now)
            return Response({'detail': '该预约时间已结束，并已记录为违规'}, status=status.HTTP_400_BAD_REQUEST)

        reservation.status = Reservation.STATUS_CHECKED_IN
        reservation.checkin_at = now
        reservation.save(update_fields=['status', 'checkin_at', 'updated_at'])
        return Response({'detail': '签到成功', 'reservation': ReservationSerializer(reservation).data})


class ReservationCheckOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        expire_overdue_reservations()
        serializer = ReservationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = Reservation.objects.select_related('user').filter(id=serializer.validated_data['reservation_id'], user=request.user).first()
        if not reservation:
            return Response({'detail': '预约不存在'}, status=status.HTTP_404_NOT_FOUND)
        if reservation.status != Reservation.STATUS_CHECKED_IN:
            return Response({'detail': '当前状态无法签退'}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.localtime(timezone.now())
        reservation.status = Reservation.STATUS_COMPLETED
        reservation.checkout_at = now
        reservation.save(update_fields=['status', 'checkout_at', 'updated_at'])
        return Response({'detail': '签退成功', 'reservation': ReservationSerializer(reservation).data})


class ReservationAdminListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        expire_overdue_reservations()
        qs = Reservation.objects.select_related('user__profile', 'seat').all()
        date_value = request.query_params.get('date')
        status_value = request.query_params.get('status')
        user_value = (request.query_params.get('user') or '').strip()
        if date_value:
            qs = qs.filter(reservation_date=date_value)
        if status_value in dict(Reservation.STATUS_CHOICES):
            qs = qs.filter(status=status_value)
        if user_value:
            if user_value.isdigit():
                qs = qs.filter(Q(user_id=int(user_value)) | Q(user__username__icontains=user_value) | Q(user__profile__nickname__icontains=user_value))
            else:
                qs = qs.filter(Q(user__username__icontains=user_value) | Q(user__profile__nickname__icontains=user_value))
        return Response(ReservationSerializer(qs, many=True).data)


class SeatAvailabilityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        expire_overdue_reservations()
        date_value = request.query_params.get('date')
        if date_value:
            try:
                parsed_date = datetime.fromisoformat(date_value).date()
            except ValueError:
                return Response({'detail': '日期格式错误'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            parsed_date = timezone.localdate()
        serializer = SeatSerializer(Seat.objects.all(), many=True, context={'reservation_date': parsed_date, 'request': request})
        return Response(serializer.data)


class SeatRemainingSlotsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        expire_overdue_reservations()
        seat = get_object_or_404(Seat, pk=pk)
        date_value = request.query_params.get('date')
        if date_value:
            try:
                parsed_date = datetime.fromisoformat(date_value).date()
            except ValueError:
                return Response({'detail': '日期格式错误'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            parsed_date = timezone.localdate()

        qs = Reservation.objects.select_related('user__profile').filter(
            seat=seat,
            reservation_date=parsed_date,
            status__in=[Reservation.STATUS_BOOKED, Reservation.STATUS_CHECKED_IN],
        ).order_by('start_time')
        occupied = [(item.get_start_datetime(), item.get_end_datetime()) for item in qs]
        free_ranges = build_free_time_ranges(parsed_date, occupied)
        bookable_ranges = [item for item in free_ranges if int((item[1] - item[0]).total_seconds() // 60) >= MIN_BOOKABLE_MINUTES]
        remaining_minutes = sum(int((end - start).total_seconds() // 60) for start, end in bookable_ranges)
        payload = {
            'seat': {
                'id': seat.id,
                'seat_code': seat.seat_code,
                'area': seat.area,
                'is_active': seat.is_active,
                'note': seat.note,
                'map_row': seat.map_row,
                'map_col': seat.map_col,
                'seat_type': seat.seat_type,
                'seat_type_label': dict(Seat.TYPE_CHOICES).get(seat.seat_type, seat.seat_type),
                'has_power': seat.has_power,
                'near_window': seat.near_window,
            },
            'reservation_date': parsed_date.isoformat(),
            'current_time': timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S'),
            'booking_window': {
                'start_time': '08:00',
                'end_time': '22:00',
            },
            'remaining_count': len(bookable_ranges),
            'remaining_minutes': remaining_minutes,
            'is_full': remaining_minutes < MIN_BOOKABLE_MINUTES,
            'remaining_ranges': [format_range_payload(start, end) for start, end in bookable_ranges],
            'occupied_ranges': [format_range_payload(start, end) for start, end in occupied],
            'occupied_reservations': ReservationSerializer(qs, many=True, context={'request': request}).data,
        }
        return Response(payload)


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        expire_overdue_reservations()
        today = timezone.localdate()
        now = timezone.localtime(timezone.now())
        month_start, month_end = _month_bounds(today)
        profile = ensure_profile(request.user)

        checkin_done_today = DailyCheckIn.objects.filter(user=request.user, checkin_date=today).exists()
        checkin_count_month = DailyCheckIn.objects.filter(
            user=request.user,
            checkin_date__gte=month_start,
            checkin_date__lte=month_end,
        ).count()

        mine_today = Reservation.objects.filter(
            user=request.user,
            reservation_date=today,
            status__in=[Reservation.STATUS_CHECKED_IN, Reservation.STATUS_COMPLETED],
        )
        study_minutes_today = _sum_study_minutes(mine_today, now)

        mine_month = Reservation.objects.filter(
            user=request.user,
            reservation_date__gte=month_start,
            reservation_date__lte=month_end,
            status__in=[Reservation.STATUS_CHECKED_IN, Reservation.STATUS_COMPLETED],
        )
        study_minutes_month = _sum_study_minutes(mine_month, now)

        base_payload = {
            'today_label': today.isoformat(),
            'month_label': f'{today.year}年{today.month}月',
            'study_minutes_today': study_minutes_today,
            'study_minutes_month': study_minutes_month,
            'checkin_done_today': checkin_done_today,
            'checkin_count_month': checkin_count_month,
            'credit_score': profile.credit_score,
            'violation_count': profile.violation_count,
        }

        if request.user.is_staff or request.user.is_superuser:
            total_seats = Seat.objects.count()
            active_seats = Seat.objects.filter(is_active=True).count()
            active_reservations = Reservation.objects.filter(status__in=[Reservation.STATUS_BOOKED, Reservation.STATUS_CHECKED_IN]).count()
            today_reservations = Reservation.objects.filter(reservation_date=today).count()
            today_checkins = DailyCheckIn.objects.filter(checkin_date=today).count()
            total_users = User.objects.count()
            material_total = LearningMaterial.objects.count()
            return Response({
                'role': 'admin',
                **base_payload,
                'seat_total': total_seats,
                'seat_active': active_seats,
                'reservation_active': active_reservations,
                'reservation_today': today_reservations,
                'checkin_today': today_checkins,
                'user_total': total_users,
                'material_total': material_total,
            })

        return Response({
            'role': 'user',
            **base_payload,
        })


class DashboardAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        expire_overdue_reservations()
        today = timezone.localdate()
        now = timezone.localtime(timezone.now())
        week_start = today - timedelta(days=6)
        month_start, month_end = _month_bounds(today)

        base_qs = Reservation.objects.select_related('seat', 'user__profile').filter(
            status__in=[Reservation.STATUS_CHECKED_IN, Reservation.STATUS_COMPLETED],
            reservation_date__gte=week_start,
            reservation_date__lte=month_end,
        )
        if not (request.user.is_staff or request.user.is_superuser):
            base_qs = base_qs.filter(user=request.user)

        week_qs = base_qs.filter(reservation_date__gte=week_start, reservation_date__lte=today)
        month_qs = base_qs.filter(reservation_date__gte=month_start, reservation_date__lte=month_end)

        weekly_chart = _daily_minutes_payload(week_qs, week_start, today, now, lambda day: day.strftime('%m-%d'))
        monthly_chart = _daily_minutes_payload(month_qs, month_start, month_end, now, lambda day: f'{day.day}日')
        week_total = sum(item['minutes'] for item in weekly_chart)
        month_total = sum(item['minutes'] for item in monthly_chart)
        week_active_days = len([item for item in weekly_chart if item['minutes'] > 0])
        month_active_days = len([item for item in monthly_chart if item['minutes'] > 0])

        checkin_dates = DailyCheckIn.objects.filter(user=request.user).values_list('checkin_date', flat=True)
        checked_dates = set(checkin_dates)
        longest_streak = _current_streak(checked_dates)

        payload = {
            'scope': 'admin' if (request.user.is_staff or request.user.is_superuser) else 'user',
            'weekly_chart': weekly_chart,
            'monthly_chart': monthly_chart,
            'weekly_report': {
                'total_minutes': week_total,
                'active_days': week_active_days,
                'average_minutes': int(week_total / 7) if weekly_chart else 0,
            },
            'monthly_report': {
                'total_minutes': month_total,
                'active_days': month_active_days,
                'average_minutes': int(month_total / max(pycalendar.monthrange(today.year, today.month)[1], 1)),
                'current_streak_days': longest_streak,
            },
        }

        if request.user.is_staff or request.user.is_superuser:
            violation_week = ViolationRecord.objects.filter(created_at__date__gte=week_start, created_at__date__lte=today).count()
            violation_month = ViolationRecord.objects.filter(created_at__date__gte=month_start, created_at__date__lte=month_end).count()
            seat_totals = {}
            for item in month_qs:
                seat_key = item.seat.seat_code
                start = item.checkin_at or item.get_start_datetime()
                end = item.checkout_at or (now if item.status == Reservation.STATUS_CHECKED_IN else item.get_end_datetime())
                if end > start:
                    seat_totals[seat_key] = seat_totals.get(seat_key, 0) + int((end - start).total_seconds() // 60)
            top_seats = [
                {'seat_code': seat_code, 'minutes': minutes}
                for seat_code, minutes in sorted(seat_totals.items(), key=lambda item: item[1], reverse=True)[:5]
            ]
            payload['system_report'] = {
                'violation_week': violation_week,
                'violation_month': violation_month,
                'top_seats': top_seats,
            }

        return Response(payload)
