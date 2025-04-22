"""
URL configuration for donation_dashboard project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_control

urlpatterns = [
    path('admin/', admin.site.urls),
    path('donations/', include('donations.urls')),


    # # ✅ Fix the login route
    # path("login/", auth_views.LoginView.as_view(template_name="donation/login.html"), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),

    # PWA URLs
    path('manifest.json', 
        cache_control(max_age=86400)(TemplateView.as_view(
            template_name='manifest.json',
            content_type='application/json',
        )),
        name='manifest.json'),
    path('serviceworker.js', 
        cache_control(max_age=86400)(TemplateView.as_view(
            template_name='serviceworker.js',
            content_type='application/javascript',
        )),
        name='serviceworker.js'),
]



# ✅ Ensure Django serves media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)