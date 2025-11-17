from django.db import models
from django.conf import settings
from django.utils import timezone

class Chat(models.Model):
    """
    留言板上的文章或留言 (原 Message)
    """
    # 關聯
    room = models.ForeignKey('rooms.Room', on_delete=models.CASCADE, related_name='chats', verbose_name='所屬房號')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='posts_and_comments', 
        verbose_name='作者'
    )
    
    # 內容
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name='標題 (文章專用)')
    content = models.TextField(verbose_name='內容')
    
    # 類型與關係 (F-5.1)
    is_article = models.BooleanField(default=True, verbose_name='是否為文章 (True=文章, False=留言/回覆)')
    
    # 父級留言/文章 (F-5.1) - 處理留言與文章的巢狀關係
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies', 
        verbose_name='父級文章/留言'
    )
    
    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    class Meta:
        verbose_name = '留言板訊息'
        verbose_name_plural = '留言板訊息'
        ordering = ['-created_at']

    def __str__(self):
        if self.is_article:
            return f"文章: {self.title or self.content[:30]}..."
        else:
            return f"回覆給 {self.parent.id} by {self.author.username}"
