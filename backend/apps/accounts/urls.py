from django.urls import path
from .views import (
    LoginView,
    ProfileView,
    RegisterView,
    ChangePasswordView,
    AdminUserListView,
    AdminUserDetailView,
    MyViolationListView,
    AdminViolationListCreateView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('violations/me/', MyViolationListView.as_view(), name='my-violations'),
    path('admin/violations/', AdminViolationListCreateView.as_view(), name='admin-violations'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
]
