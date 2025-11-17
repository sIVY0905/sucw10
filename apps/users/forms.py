# from django import forms # <-- 引入 forms 模組是關鍵修正
# from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
# from .models import User
# # 移除了 from django.db import models，因為不再需要

# class CustomUserCreationForm(UserCreationForm):
#     """
#     客製化註冊表單，用於首次創建使用者時。
#     新增 room_number 和 room_password 欄位。
#     """
#     # 這些是表單獨有的欄位，用於創建房號，必須使用 forms.Field
#     # room_number = forms.CharField(max_length=50, label='房號') # <-- 使用 forms.CharField
#     # room_password = forms.CharField(widget=forms.PasswordInput, max_length=128, label='房號密碼') # <-- 使用 forms.CharField
    
#     class Meta:
#         model = User
#         # UserCreationForm 預設會處理 password 欄位
#         # 自定義欄位 (room_number/room_password) 在類別屬性中定義，不需放在 fields 元組中
#         fields = ('username', 'email')

#     # def __init__(self, *args, **kwargs):
#     #     super().__init__(*args, **kwargs)
#     #     # 確保密碼欄位提示文本被移除
#     #     if 'password' in self.fields:
#     #         self.fields['password'].help_text = None
        
# class CustomAuthenticationForm(AuthenticationForm):
#     """
#     客製化登入表單，使用姓名(username)和密碼進行認證。
#     """
#     class Meta:
#         model = User
#         fields = ('username', 'password')


# apps/users/forms.py (最終確認版)
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

# 1. 用於註冊 (SignUpView)
class CustomUserCreationForm(UserCreationForm):
    """
    用於註冊流程的表單。
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email') # 確保只包含您在 models.py 中規劃的欄位

# 2. 用於 Admin 介面 (解決當前 ImportError 的關鍵)
class CustomUserChangeForm(UserChangeForm):
    """
    用於 Admin 編輯流程的表單。
    """
    class Meta:
        model = User
        # 必須包含 Admin 介面需要的所有欄位，例如權限相關的
        fields = ('username', 'email', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')