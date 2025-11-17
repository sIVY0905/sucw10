from django.urls import path
from .views import HomeView, ChoreListView, ChoreCreateView, ChoreUpdateView, ChoreDeleteView, ChoreCompleteView
from . import views
# 確保從 .views 導入了所有需要的 View

app_name = 'chores'

urlpatterns = [
    # 修正點 1：將根路徑 (chores/) 指向 ChoreListView
    path('', views.ChoreListView.as_view(), name='list'), # 舊名可能是 'home'

    # 修正點 2：如果您仍需要儀表板（HomeView），可以給它一個新的路徑
    path('dashboard/', views.HomeView.as_view(), name='home'),
    # 家務清單與統計 (F-3.1, F-3.2, F-3.4)
    # path('list/', views.ChoreListView.as_view(), name='list'), 
    
    # CRUD 操作 (F-3.3)
    path('new/', views.ChoreCreateView.as_view(), name='create'),
    path('edit/<int:pk>/', views.ChoreUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', views.ChoreDeleteView.as_view(), name='delete'),
    
    # 家務完成 AJAX (用於 HomeView 中的勾選)
    path('complete/<int:pk>/', views.ChoreCompleteView.as_view(), name='complete'),
]
