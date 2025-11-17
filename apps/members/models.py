from django.db import models
from django.conf import settings
# from apps.rooms.models import Room
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Member(models.Model):
    room = models.ForeignKey('rooms.Room', on_delete=models.CASCADE, related_name='member_links', verbose_name='所屬房號')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships', verbose_name='使用者')
    joined_at = models.DateTimeField(default=timezone.now, verbose_name='加入時間')

    class Meta:
        verbose_name = '房間成員'
        verbose_name_plural = '房間成員'

    def __str__(self):
        return f"{self.user} in {self.room}"
