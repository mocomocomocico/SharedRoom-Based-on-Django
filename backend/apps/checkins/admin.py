from django.contrib import admin

from .models import DailyCheckIn


@admin.register(DailyCheckIn)
class DailyCheckInAdmin(admin.ModelAdmin):
    list_display = ('user', 'checkin_date', 'created_at')
    search_fields = ('user__username', 'user__profile__nickname')
    list_filter = ('checkin_date',)
