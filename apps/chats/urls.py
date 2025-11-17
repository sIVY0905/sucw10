from django.urls import path
from apps.chats import views

app_name = 'chats' # ***App Name 變更***

urlpatterns = [
    # 列表與新增文章
    path('', views.ChatListView.as_view(), name='list'), # ***View 名稱變更***
    path('new/', views.ArticleCreateView.as_view(), name='create'),
    
    # 文章詳情與留言發布 (F-5.4)
    path('<int:pk>/', views.ChatDetailView.as_view(), name='detail'), # ***View 名稱變更***
    path('<int:pk>/reply/', views.ReplyCreateView.as_view(), name='reply'),
    # 編輯/刪除 (F-5.3) - 待實作
]