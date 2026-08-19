from django.contrib import admin
from .models import Seat, TimeSlot

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('seat_code', 'area', 'is_active', 'note', 'updated_at')
    list_filter = ('area', 'is_active')
    search_fields = ('seat_code', 'area', 'note')
    list_editable = ('is_active',)
    ordering = ('seat_code',)
    actions = ['make_active', 'make_inactive']

    @admin.action(description='设为可用')
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='设为不可用')
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_editable = ('is_active', 'sort_order')
    ordering = ('sort_order', 'start_time')
