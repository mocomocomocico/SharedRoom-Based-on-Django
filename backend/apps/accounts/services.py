# 用户信用分服务：把违规记录创建和信用分扣减放在同一个事务中，避免数据不一致。
from django.db import transaction

from .models import UserProfile, ViolationRecord


def ensure_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


@transaction.atomic
def create_violation_record(*, user, reason, score_delta=-10, violation_type=ViolationRecord.TYPE_OTHER, reservation=None, created_by=None):
    if reservation is not None:
        existing = ViolationRecord.objects.filter(
            user=user,
            reservation=reservation,
            violation_type=violation_type,
        ).first()
        if existing:
            return existing, False

    record = ViolationRecord.objects.create(
        user=user,
        reservation=reservation,
        created_by=created_by,
        violation_type=violation_type,
        reason=reason,
        score_delta=score_delta,
    )
    profile = ensure_profile(user)
    profile.credit_score = max(0, profile.credit_score + score_delta)
    profile.violation_count += 1
    profile.save(update_fields=['credit_score', 'violation_count'])
    return record, True
