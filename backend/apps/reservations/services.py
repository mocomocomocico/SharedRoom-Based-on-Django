# 预约业务服务：封装逾期未签到等违规判定逻辑，供视图层复用。
from django.utils import timezone

from apps.accounts.models import ViolationRecord
from apps.accounts.services import create_violation_record

from .models import Reservation


NO_SHOW_PENALTY = -15


def mark_no_show_violation(reservation, now=None):
    now = now or timezone.localtime(timezone.now())
    return create_violation_record(
        user=reservation.user,
        reservation=reservation,
        violation_type=ViolationRecord.TYPE_NO_SHOW,
        reason=f'预约座位 {reservation.seat.seat_code} 未在签到截止前签到，已记为爽约',
        score_delta=NO_SHOW_PENALTY,
    )


def expire_overdue_reservations(now=None):
    now = now or timezone.localtime(timezone.now())
    changed = []
    qs = Reservation.objects.select_related('seat', 'user').filter(
        status__in=[Reservation.STATUS_BOOKED, Reservation.STATUS_CHECKED_IN]
    )
    for reservation in qs:
        end_dt = reservation.get_end_datetime()
        deadline = reservation.get_checkin_deadline()

        if reservation.status == Reservation.STATUS_BOOKED and now >= deadline:
            reservation.status = Reservation.STATUS_EXPIRED
            reservation.cancelled_at = reservation.cancelled_at or now
            changed.append(reservation)
            mark_no_show_violation(reservation, now)
            continue

        if reservation.status == Reservation.STATUS_CHECKED_IN and now >= end_dt:
            reservation.status = Reservation.STATUS_COMPLETED
            reservation.checkout_at = reservation.checkout_at or end_dt
            changed.append(reservation)

    if changed:
        Reservation.objects.bulk_update(changed, ['status', 'cancelled_at', 'checkout_at', 'updated_at'])
    return len(changed)
