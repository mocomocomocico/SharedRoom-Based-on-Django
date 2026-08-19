# 预约时间工具：集中处理预约时间、可预约范围、区间合并与前端展示格式。
from datetime import datetime, timedelta, time as time_cls

from django.utils import timezone

# 全局预约规则：每天 08:00-22:00 可预约，单次至少 30 分钟。
RESERVABLE_START_TIME = time_cls(8, 0)
RESERVABLE_END_TIME = time_cls(22, 0)
MIN_BOOKABLE_MINUTES = 30


def _to_aware(day_date, day_time):
    tz = timezone.get_current_timezone()
    return timezone.make_aware(datetime.combine(day_date, day_time), tz)


def get_reservation_start_datetime(reservation_or_date, start_time=None):
    if hasattr(reservation_or_date, 'reservation_date'):
        reservation_date = reservation_or_date.reservation_date
        start_time = reservation_or_date.start_time
    else:
        reservation_date = reservation_or_date
    return _to_aware(reservation_date, start_time)


def get_reservation_end_datetime(reservation_or_date, end_time=None):
    if hasattr(reservation_or_date, 'reservation_date'):
        reservation_date = reservation_or_date.reservation_date
        end_time = reservation_or_date.end_time if end_time is None else end_time
    else:
        reservation_date = reservation_or_date
    return _to_aware(reservation_date, end_time)


def get_reservation_checkin_deadline(reservation):
    return get_reservation_start_datetime(reservation) + timedelta(minutes=15)


def time_ranges_overlap(start_a, end_a, start_b, end_b):
    return max(start_a, start_b) < min(end_a, end_b)


def merge_intervals(intervals):
    """合并相互重叠的占用区间，便于后续一次性计算空闲时间。"""
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    merged = [list(intervals[0])]
    for start, end in intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1][1] = max(last_end, end)
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def build_free_time_ranges(day_date, occupied_intervals, now=None):
    """根据占用区间反推当天可预约时间；如果查询今天，会自动跳过已过去的时间。"""
    now = now or timezone.localtime(timezone.now())
    tz = timezone.get_current_timezone()
    day_start = timezone.make_aware(datetime.combine(day_date, RESERVABLE_START_TIME), tz)
    day_end = timezone.make_aware(datetime.combine(day_date, RESERVABLE_END_TIME), tz)

    if day_date == now.date():
        cursor = max(day_start, now)
    else:
        cursor = day_start

    clipped = []
    for start_dt, end_dt in merge_intervals(occupied_intervals):
        if end_dt <= cursor or start_dt >= day_end:
            continue
        clipped.append((max(start_dt, cursor), min(end_dt, day_end)))

    free_ranges = []
    pointer = cursor
    for start_dt, end_dt in clipped:
        if pointer < start_dt:
            free_ranges.append((pointer, start_dt))
        pointer = max(pointer, end_dt)
    if pointer < day_end:
        free_ranges.append((pointer, day_end))

    return free_ranges


def format_range_payload(start_dt, end_dt):
    """把后端 datetime 区间转成前端按钮可以直接展示的结构。"""
    duration = int((end_dt - start_dt).total_seconds() // 60)
    return {
        'start_time': start_dt.strftime('%H:%M'),
        'end_time': end_dt.strftime('%H:%M'),
        'label': f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}",
        'duration_minutes': duration,
    }
