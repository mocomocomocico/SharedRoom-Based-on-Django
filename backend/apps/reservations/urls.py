from django.urls import path
from .views import (
    ReservationMineView,
    ReservationBookView,
    ReservationCancelView,
    ReservationAdminListView,
    ReservationCheckInView,
    ReservationCheckOutView,
    SeatAvailabilityView,
    SeatRemainingSlotsView,
    DashboardSummaryView,
    DashboardAnalyticsView,
)

urlpatterns = [
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('dashboard/analytics/', DashboardAnalyticsView.as_view(), name='dashboard-analytics'),
    path('seats/availability/', SeatAvailabilityView.as_view(), name='seat-availability'),
    path('seats/<int:pk>/remaining-slots/', SeatRemainingSlotsView.as_view(), name='seat-remaining-slots'),
    path('reservations/book/', ReservationBookView.as_view(), name='reservation-book'),
    path('reservations/cancel/', ReservationCancelView.as_view(), name='reservation-cancel'),
    path('reservations/checkin/', ReservationCheckInView.as_view(), name='reservation-checkin'),
    path('reservations/checkout/', ReservationCheckOutView.as_view(), name='reservation-checkout'),
    path('reservations/my/', ReservationMineView.as_view(), name='reservation-mine'),
    path('reservations/admin/', ReservationAdminListView.as_view(), name='reservation-admin-list'),
]
