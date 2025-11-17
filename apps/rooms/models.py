
from django.db import models
from django.conf import settings
from django.urls import reverse

class Room(models.Model):
    """
    房號模型，定義一個合住單位。
    """
    room_number = models.CharField(max_length=50, unique=True, verbose_name='房號')
    password = models.CharField(max_length=128, verbose_name='房號密碼 (儲存 Hashed 值)')
    
    # 修正 1: 確保 members 的反向關聯名稱唯一
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='joined_rooms', # <-- 將 'rooms_joined' 改為 'joined_rooms'
        verbose_name='房號成員'
    )
    
    # 修正 2: 確保 creator 的反向關聯名稱唯一
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_rooms', # <-- 將 'rooms_created' 改為 'created_rooms'
        verbose_name='創建者'
    )

    class Meta:
        verbose_name = '房號'
        verbose_name_plural = '房號'

    def __str__(self):
        return self.room_number


# Create your models here.
