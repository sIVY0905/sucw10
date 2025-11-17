from django.db import models
from django.conf import settings
from apps.rooms.models import Room
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
# 引入自定義管理器
from .managers import ChoreManager

class Chore(models.Model):
    """家務事項模型"""
    
    CHORE_TYPES = [
        ('PUBLIC', '公共家事'),
        ('PRIVATE', '私人家事'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='chores', verbose_name='所屬房號')
    title = models.CharField(max_length=100, verbose_name='家務名稱')
    type = models.CharField(max_length=10, choices=CHORE_TYPES, default='PUBLIC', verbose_name='類型')
    
    # 頻率，單位為天 (例如 7 天一次)
    frequency_days = models.PositiveIntegerField(default=7, verbose_name='頻率 (天)')
    
    # 上次紀錄：上次完成的日期 (用於計算下次應完成日期)
    last_completed = models.DateField(default=timezone.now, verbose_name='上次完成日期')

    # 負責成員 (公共家事用於輪值，私人家事則為固定負責人)
    assigned_to = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='assigned_chores', verbose_name='負責成員')
    
    # 私人家務區域細分
    private_area = models.CharField(max_length=100, blank=True, null=True, verbose_name='私人家務區域')

    # 使用自定義管理器
    objects = ChoreManager()

    @property
    def next_due_date(self):
        """計算下一次應完成的日期 (僅限 Python 內部使用，不可用於 ORM 查詢)"""
        if self.frequency_days is None:
            return None
        
        # 使用上次完成時間 + 頻率
        return (self.last_completed.date() + timedelta(days=self.frequency_days))

    class Meta:
        verbose_name = '家務事項'
        verbose_name_plural = '家務事項'
        ordering = ['last_completed']

    def __str__(self):
        return f"{self.room.room_number} - {self.title}"

class ChoreRecord(models.Model):
    """家務完成紀錄模型"""
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE, related_name='records', verbose_name='家務事項')
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='完成者')
    completed_on = models.DateTimeField(auto_now_add=True, verbose_name='實際完成時間')

    class Meta:
        verbose_name = '家務完成紀錄'
        verbose_name_plural = '家務完成紀錄'
        ordering = ['-completed_on']

    def __str__(self):
        return f"{self.chore.title} 於 {self.completed_on.strftime('%Y-%m-%d')}"

# Create your models here.
