"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]


from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import login_user, refresh_token

# Import JWT views optionally to avoid startup error when pkg_resources is missing
try:
    from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
    _JWT_AVAILABLE = True
except Exception:
    _JWT_AVAILABLE = False

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('medications/', include('medications.urls')),
    path('scheduling/', include('scheduling.urls')),
    path('notifications/', include('notifications.urls')),
    path('reports/', include('reports.urls')),
    path('api/', include('api.urls')),
]

if _JWT_AVAILABLE:
    urlpatterns += [
        path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ]
else:
    urlpatterns += [
        path('api/token/', login_user, name='token_obtain_pair'),
        path('api/token/refresh/', refresh_token, name='token_refresh'),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "نظام إدارة الأدوية الذكي"
admin.site.site_title = "لوحة التحكم"
admin.site.index_title = "مرحباً بك في نظام إدارة الأدوية"