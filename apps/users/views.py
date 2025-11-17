from django.shortcuts import render
# apps/users/views.py (補齊)
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .models import User # 確保導入您的自定義 User 模型
from .forms import CustomUserCreationForm # 需要創建這個 Form

# 假設您使用的是內建的 UserCreationForm，如果不是，需要自行定義
class SignUpView(CreateView):
    form_class = CustomUserCreationForm# 假設這個 Form 存在於 apps/users/forms.py 中
    success_url = reverse_lazy('chores:home')
    model = User
