from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    """
    客製化使用者模型。用於處理單一使用者帳號對應多個房號的需求。
    
    欄位說明:
    - username: 姓名 (用於登入)
    - email: 郵件信箱 (全域唯一)
    - password: 個人密碼
    - rooms: ManyToManyField 連結到 Room (定義在 rooms/models.py)
    """
    
    # 移除標準的 username 欄位（我們將使用姓名作為登入名稱）
    # 或者直接使用 AbstractUser 的 username 欄位來存儲姓名
    # 如果想用 email 登入，需要進一步客製化
    # 這裡假設我們沿用 AbstractUser 的欄位作為姓名/登入名稱

    email = models.EmailField(unique=True, verbose_name='郵件信箱')

    # 確保不會使用標準的 username 欄位
    USERNAME_FIELD = 'email'  # 如果要用 email 登入
    REQUIRED_FIELDS = ['username']

    # 後續會加入 rooms 的 ManyToMany 關係
    
    class Meta:
        verbose_name = '使用者'
        verbose_name_plural = '使用者'

    def __str__(self):
        return self.username
    
    # 輔助屬性：取得使用者當前選擇的房號 (用於 HomeView 查詢)
    # 實際應用中，這會存儲在 Session 或另一個 Profile 模型中
   


# Create your models here.
