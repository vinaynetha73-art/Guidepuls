from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from emergency.views import home_page, emergency_home
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home_page, name='home'),          # HOME
    path('emergency/', emergency_home, name='emergency'),

    path('', include('accounts.urls')),


]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
