# 每日打卡接口：完成打卡、查询今日状态和历史记录。
from calendar import Calendar
from datetime import date
import calendar as pycalendar

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DailyCheckIn
from .serializers import DailyCheckInSerializer


def _get_month_bounds(year: int, month: int):
    last_day = pycalendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def _build_calendar_payload(year: int, month: int, checked_dates: set[str]):
    cal = Calendar(firstweekday=0)
    weeks = []
    today = timezone.localdate()
    month_name = f'{year}年{month}月'

    for week in cal.monthdatescalendar(year, month):
        row = []
        for day in week:
            day_str = day.isoformat()
            in_month = day.month == month
            row.append({
                'date': day_str,
                'day': day.day,
                'in_month': in_month,
                'is_today': day == today,
                'checked': day_str in checked_dates,
            })
        weeks.append(row)

    return {
        'year': year,
        'month': month,
        'month_label': month_name,
        'weeks': weeks,
        'checked_dates': sorted(checked_dates),
    }


class DailyCheckInCalendarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        try:
            year = int(year) if year else today.year
            month = int(month) if month else today.month
            if not 1 <= month <= 12:
                raise ValueError
        except ValueError:
            return Response({'detail': '年月参数格式错误'}, status=status.HTTP_400_BAD_REQUEST)

        start_date, end_date = _get_month_bounds(year, month)
        checkins = DailyCheckIn.objects.filter(
            user=request.user,
            checkin_date__gte=start_date,
            checkin_date__lte=end_date,
        ).values_list('checkin_date', flat=True)
        checked_dates = {item.isoformat() for item in checkins}

        payload = _build_calendar_payload(year, month, checked_dates)
        payload['checked_count'] = len(checked_dates)
        payload['month_days'] = end_date.day
        payload['today'] = today.isoformat()
        return Response(payload)


class DailyCheckInTodayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        today = timezone.localdate()
        checkin, created = DailyCheckIn.objects.get_or_create(
            user=request.user,
            checkin_date=today,
        )
        if created:
            serializer = DailyCheckInSerializer(checkin)
            return Response({
                'detail': '今日打卡成功',
                'checkin': serializer.data,
            }, status=status.HTTP_201_CREATED)
        return Response({
            'detail': '今日已经打卡过了',
            'checkin': DailyCheckInSerializer(checkin).data,
        })
