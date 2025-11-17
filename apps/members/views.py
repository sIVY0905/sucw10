from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from apps.rooms.models import Room # 假設 Room 在 apps.rooms
from apps.chores.models import ChoreRecord # 假設 ChoreRecord 在 apps.chores
from django.conf import settings # 獲取 AUTH_USER_MODEL
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
#from apps.members.forms import MemberForm  假設已導入 MemberForm
from .models import Member # 假設已導入 Member
from apps.chats.models import Chat

# 沿用 HomeView 的邏輯來獲取當前房間
def get_current_room(request):
    """輔助函數：獲取當前用戶和房號。"""
    current_room_id = request.session.get('current_room_id') 
    try:
        room = Room.objects.get(id=current_room_id, members=request.user)
        return room
    except (Room.DoesNotExist, TypeError):
        return None

class MemberListView(LoginRequiredMixin, ListView):
    template_name = 'members/member_list.html'
    context_object_name = 'members_data'
    
    def get_queryset(self):
        self.room = get_current_room(self.request)
        
        if not self.room:
            # 如果沒有房間，返回空的 QuerySet
            return settings.AUTH_USER_MODEL.objects.none()
        # 獲取當前房間的所有成員 (使用我們在 rooms/models.py 中定義的反向查詢名稱 'joined_rooms')
        # 為了安全，使用 filter(rooms=self.room) 或 self.room.members.all()
        return settings.AUTH_USER_MODEL.objects.filter(joined_rooms=self.room)
        # # 獲取當前房號的所有成員
        # members = self.room.members.all()
        
        # # 統計成員的家務完成紀錄數
        # # 使用 annotate 和 Subquery/Count 可以在單個查詢中完成，但為了簡潔和可讀性，我們使用 Python 處理統計
        
        # # 1. 獲取當前房號下所有家務的紀錄
        # room_chore_records = ChoreRecord.objects.filter(
        #     chore__room=self.room
        # )
        
        # members_data = []
        # for member in members:
        #     # 計算該成員完成的家務總數
        #     completed_count = room_chore_records.filter(completed_by=member).count()
            
        #     # 這裡可以加入更多統計，例如：
        #     # - 負責的家務數 (Chore.objects.filter(assigned_to=member, room=self.room).count())
        #     # - 留言板文章數 (依賴 messages App)
            
        #     members_data.append({
        #         'user': member,
        #         'completed_chores_count': completed_count,
        #         # 'message_count': message_count, # 待加入
        #     })
            
        # return members_data # 返回的是一個包含字典的 List

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room'] = self.room
        if not self.room:
             context['no_room_assigned'] = True
             
        return context


class MemberDetailView(LoginRequiredMixin, DetailView):
    # 這裡的 model 應指向 User 模型，但因為我們無法直接繼承 User，
    # 且目標是顯示特定用戶的資料，我們將手動查詢 User 模型。
    template_name = 'members/member_detail.html'
    context_object_name = 'target_member'
    
    # 覆寫 get_object 來處理用戶 PK 查詢和房間驗證
    def get_object(self, queryset=None):
        self.room = get_current_room(self.request)
        if not self.room:
            # 如果用戶沒有房間，我們無法顯示任何成員細節
            return None 

        member_pk = self.kwargs.get('pk')
        # 獲取目標成員，並確保該成員在當前房間內
        target_member = get_object_or_404(
            settings.AUTH_USER_MODEL.objects.filter(joined_rooms=self.room), 
            pk=member_pk
        )
        return target_member

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target_member = context['target_member']
        
        if not target_member:
            context['no_room_assigned'] = True
            return context

        # -------------------- F-4.2 留言板內容 --------------------
        # 獲取該成員在當前房間內發布的所有文章和留言/回覆
        member_chats = Chat.objects.filter(
            author=target_member, 
            room=self.room
        ).order_by('-created_at')
        
        # 分類為文章和留言
        member_articles = member_chats.filter(is_article=True)
        member_replies = member_chats.filter(is_article=False).select_related('parent')
        
        context['articles_count'] = member_articles.count()
        context['replies_count'] = member_replies.count()
        context['member_articles'] = member_articles[:10] # 只顯示最新的10篇文章
        context['member_replies'] = member_replies[:10]   # 只顯示最新的10條留言
        
        # -------------------- 家務統計 (F-4.1 延伸) --------------------
        # 計算該成員完成的家務總數
        completed_chores_count = ChoreRecord.objects.filter(
            completed_by=target_member,
            chore__room=self.room
        ).count()
        
        context['completed_chores_count'] = completed_chores_count
        context['room'] = self.room
        
        return context