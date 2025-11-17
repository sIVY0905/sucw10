from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm

# 繼承內建的 UserAdmin 並使用我們自定義的表單
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    
    list_display = ['username', 'email', 'is_staff'] # 列表顯示欄位
    # 定義在 Admin 介面中顯示的欄位組
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    #  用於新增使用者的欄位設定
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    

# 註冊自定義 User 模型與 Admin 類別
admin.site.register(User, CustomUserAdmin)
