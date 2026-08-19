from django.urls import path

from .views import SeatListCreateView, SeatDetailView, TimeSlotListCreateView, TimeSlotDetailView

urlpatterns = [
    path('seats/', SeatListCreateView.as_view(), name='seat-list-create'),
    path('seats/<int:pk>/', SeatDetailView.as_view(), name='seat-detail'),
    path('slots/', TimeSlotListCreateView.as_view(), name='slot-list-create'),
    path('slots/<int:pk>/', TimeSlotDetailView.as_view(), name='slot-detail'),
]
