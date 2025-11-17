from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404

from .models import Chat # ***模型名稱變更為 Chat***
from .forms import ArticleForm, ReplyForm # 確保已導入
from apps.rooms.models import Room 


# 定義輔助函數
def get_current_room(request):
    """輔助函數：獲取當前用戶和房號。"""
    current_room_id = request.session.get('current_room_id') 
    try:
        # 這裡假設 Room 模型有一個 members 欄位/關係
        room = Room.objects.get(id=current_room_id, members=request.user) 
        return room
    except (Room.DoesNotExist, TypeError):
        return None

class ChatListView(LoginRequiredMixin, ListView): # ***類別名稱變更為 ChatListView***
    model = Chat # ***使用 Chat 模型***
    template_name = 'chats/chat_list.html' # ***模板路徑變更***
    context_object_name = 'articles'
    
    def get_queryset(self):
        self.room = get_current_room(self.request)
        if not self.room:
            return Chat.objects.none()
        # F-5.2: 僅顯示文章 (is_article=True)
        return Chat.objects.filter(room=self.room, is_article=True).select_related('author').prefetch_related('replies').order_by('-created_at')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room'] = self.room
        if not self.room:
            context['no_room_assigned'] = True
        return context
    
    # ... (get_context_data 保持不變)

class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Chat # ***使用 Chat 模型***
    form_class = ArticleForm
    template_name = 'chats/article_form.html' # ***模板路徑變更***
    def get_success_url(self):
        # 創建成功後導向文章詳情頁
        return reverse('chats:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        self.room = get_current_room(self.request)
        if not self.room:
            # 如果用戶沒有房間，阻止創建
            form.add_error(None, "您尚未加入房號，無法發布文章。")
            return self.form_invalid(form)

        form.instance.author = self.request.user
        form.instance.room = self.room
        form.instance.is_article = True  # 標記為文章
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room'] = get_current_room(self.request)
        return context


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    """F-5.3 編輯文章"""
    model = Chat
    form_class = ArticleForm
    template_name = 'chats/article_form.html'
    
    def get_queryset(self):
        # 確保用戶只能編輯自己且是文章的內容
        return Chat.objects.filter(author=self.request.user, is_article=True)

    def get_success_url(self):
        return reverse('chats:detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room'] = get_current_room(self.request)
        return context

class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    """F-5.3 刪除文章"""
    model = Chat
    success_url = reverse_lazy('chats:list')
    template_name = 'chats/article_confirm_delete.html' # 需要創建刪除確認模板
    
    def get_queryset(self):
        # 確保用戶只能刪除自己且是文章的內容
        return Chat.objects.filter(author=self.request.user, is_article=True)

class ChatDetailView(LoginRequiredMixin, DetailView): # ***類別名稱變更為 ChatDetailView***
    """F-5.4 文章詳情與留言顯示"""
    model = Chat # ***使用 Chat 模型***
    template_name = 'chats/chat_detail.html' # ***模板路徑變更***
    context_object_name = 'article'
    # ... (get_queryset 和 get_context_data 保持不變，但內部引用應改為 Chat.objects 和 'replies' 關係)
    def get_queryset(self):
        self.room = get_current_room(self.request)
        if not self.room:
            return Chat.objects.none()
        
        # 確保只能看到當前房間內且是文章的內容
        return Chat.objects.filter(room=self.room, is_article=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = context['article']
        
        # 獲取所有留言，並使用 select_related('author')
        context['comments'] = article.replies.filter(
            is_article=False
        ).select_related('author').order_by('created_at')
        
        context['reply_form'] = ReplyForm() # 傳遞空留言表單
        context['room'] = self.room
        return context

class ReplyCreateView(LoginRequiredMixin, CreateView):
    model = Chat
    form_class = ReplyForm
    # 這裡不使用模板，處理完畢直接重定向回文章詳情頁面

    def form_valid(self, form):
        room = get_current_room(self.request)
        article = get_object_or_404(Chat, pk=self.kwargs['pk'], is_article=True, room=room)
        
        form.instance.author = self.request.user
        form.instance.room = room
        form.instance.is_article = False # 確保是留言
        form.instance.parent = article   # 指定父級文章
        return super().form_valid(form)

    def get_success_url(self):
        # 提交成功後重定向回文章詳情頁面
        return reverse('chats:detail', kwargs={'pk': self.kwargs['pk']})

# 注意：您可能還需要處理 ChatDetailView 中的 POST 請求，以確保表單驗證失敗時能正確渲染錯誤信息。