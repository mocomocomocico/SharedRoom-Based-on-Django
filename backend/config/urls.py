# 全局路由入口：汇总各业务模块 API，并在开发环境暴露媒体文件访问。
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/', include('apps.seats.urls')),
    path('api/', include('apps.reservations.urls')),
    path('api/', include('apps.checkins.urls')),
    path('api/', include('apps.materials.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
