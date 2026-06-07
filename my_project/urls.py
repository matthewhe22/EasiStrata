"""my_project URL Configuration

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
from base import views as base_view
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from my_project import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', base_view.IndexView.as_view(), name='homepage'),
    path('base/', include('base.urls'), name='base'),
    path('property/', include('property.urls'), name='property'),
    path('finance/', include('finance.urls'), name='finance'),
    path('strata/', include('strata.urls'), name='strata'),
    # path('strata/', include('strata.urls'), name='strata'),

]
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)