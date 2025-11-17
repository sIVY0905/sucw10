"""
URL configuration for roomie_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path, include
from django.shortcuts import redirect
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    
    # 各 App 的路由
    path('members/', include('apps.members.urls')),  # <-- 新增
    path('chats/', include('apps.chats.urls')),      # <-- 新增
    
    # 處理用戶認證和 Room 選擇的 App
    path('auth/', include('apps.users.urls')), 
    path('rooms/', include('apps.rooms.urls')), 
    path('accounts/', include('allauth.urls')),  # <-- 使用預設
    
    # 將主頁設定為 chores:home
    path('chores/', include('apps.chores.urls')),

    # 將根路徑導向到主頁
    path('', RedirectView.as_view(url='/rooms/', permanent=False)),
]
