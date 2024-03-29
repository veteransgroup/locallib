"""locallib URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.conf.urls import include, url
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from catalog import views
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    # path('accounts/', include('django.contrib.auth.urls')),
    path('catalog/', include('catalog.urls')),
    path('help/', views.intro, name='introduction'),
    path('', RedirectView.as_view(url='/catalog/', permanent=True)),
    path('accounts/<int:pk>', views.UserDetailView.as_view(), name='user-detail'),
    path('accounts/<int:pk>/update/',
         views.UserUpdateView.as_view(), name='user_update'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [url(r'^static/(?P<path>.*)$', serve,
                        {'document_root': settings.STATIC_ROOT})]
    urlpatterns += [url(r'^uploads/(?P<path>.*)$', serve,
                        {'document_root': settings.MEDIA_ROOT})]
