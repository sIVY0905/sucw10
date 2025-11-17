# rooms/urls.py (新增)
from django.urls import path
from . import views

app_name = 'rooms'

urlpatterns = [
    # 顯示用戶所有房間並提供創建/加入選項
    path('', views.RoomListView.as_view(), name='list'),
    
    # 處理切換當前房間 (透過 URL 傳遞 ID)
    path('select/<int:room_id>/', views.SelectRoomView.as_view(), name='select'),
    # 處理創建和加入房間
    path('create/', views.CreateRoomView.as_view(), name='create'), # <-- 新增
    path('join/', views.JoinRoomView.as_view(), name='join'),       # <-- 新增
    # 【關鍵修正】：新增 'members/' 路由，指向一個新的 View
    path('members/', views.RoomMembersView.as_view(), name='members'), # <--- 新增這行
]