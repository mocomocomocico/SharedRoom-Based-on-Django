from django.urls import path

from .views import DailyCheckInCalendarView, DailyCheckInTodayView

urlpatterns = [
    path('checkins/calendar/', DailyCheckInCalendarView.as_view(), name='checkin-calendar'),
    path('checkins/today/', DailyCheckInTodayView.as_view(), name='checkin-today'),
]
