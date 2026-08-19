from django.urls import path

from .views import LearningMaterialListCreateView, LearningMaterialDetailView, LearningMaterialDownloadView

urlpatterns = [
    path('materials/', LearningMaterialListCreateView.as_view(), name='learning-material-list-create'),
    path('materials/<int:pk>/download/', LearningMaterialDownloadView.as_view(), name='learning-material-download'),
    path('materials/<int:pk>/', LearningMaterialDetailView.as_view(), name='learning-material-detail'),
]
