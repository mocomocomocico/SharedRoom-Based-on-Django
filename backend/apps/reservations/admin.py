from django.contrib import admin
from django.utils import timezone
from .models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'seat', 'reservation_date', 'time_slot', 'status', 'created_at', 'cancelled_at')
    list_filter = ('status', 'reservation_date', 'time_slot', 'seat')
    search_fields = ('user__username', 'seat__seat_code', 'time_slot__name')
    date_hierarchy = 'reservation_date'
    actions = ['mark_cancelled']

    @admin.action(description='批量取消预约')
    def mark_cancelled(self, request, queryset):
        queryset.filter(status=Reservation.STATUS_BOOKED).update(status=Reservation.STATUS_CANCELLED, cancelled_at=timezone.now())
