# members/urls.py (新增)
from django.urls import path
from apps.members import views


app_name = 'members'

urlpatterns = [
    # /members/
    path('', views.MemberListView.as_view(), name='list'),
    
    # /members/detail/1/ (F-4.2) - 尚未實作
    path('detail/<int:pk>/', views.MemberDetailView.as_view(), name='detail'),
]