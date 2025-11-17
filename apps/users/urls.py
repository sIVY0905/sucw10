# users/urls.py (新增)
from django.urls import path, include
from . import views # 用於自定義註冊
from django.contrib.auth import views as auth_views
from .views import SignUpView


app_name = 'users'

urlpatterns = [

    # 自定義註冊 View (需要創建)
    path('signup/', views.SignUpView.as_view(
        template_name='users/signup.html' # <--- 修正 signup 模板
    ), name='signup'),

    path('login/', auth_views.LoginView.as_view(
        template_name='users/login.html' # <--- 使用 apps/users/templates/users/login.html
    ), name='login'), 
    # 登出 (LogoutView)
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # 內建認證 Views (其餘: password_reset, password_change 等)
    # Keep this include after our overrides so it doesn't shadow them.
    path('', include('allauth.urls')), 
    # 暫時保持簡單，主要依賴內建的 auth.urls
    # 實際使用時，您需要提供 accounts/login.html, accounts/logout.html 等模板
    # 密碼重置 (新增這四行)
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), name='password_reset_complete'),
]