from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, FormView, ListView
from .models import Room
from django.urls import reverse # 需要導入
from .forms import CreateRoomForm, JoinRoomForm
from django.urls import reverse_lazy

class SelectRoomView(LoginRequiredMixin, View):
    """處理用戶選擇或切換房間的邏輯"""
    # 這裡應包含創建房間、加入房間和切換房間的邏輯
    # 為了簡化，我們只實作切換邏輯。
    
    def get(self, request, *args, **kwargs):
        room_id = kwargs.get('room_id')
        
        # 1. 確保房間存在且用戶是成員
        try:
            room = Room.objects.get(id=room_id, members=request.user)
        except Room.DoesNotExist:
            # 處理房間不存在或用戶不是成員的錯誤
            return redirect(reverse('rooms:list'))

        # 2. 設置 session 變數為當前工作房間
        request.session['current_room_id'] = room.id
        
        # 3. 導向主頁
        return redirect('chores:home')
    
    # 您還需要一個 CreateRoomView 和 JoinRoomView

class RoomListView(LoginRequiredMixin, View):
    """顯示用戶當前所有房號，並提供創建/加入房號的入口"""
    def get(self, request):
        user_rooms = Room.objects.filter(members=request.user)
        # 獲取當前房間 ID，用於標記
        current_room_id = request.session.get('current_room_id')
        
        context = {
            'user_rooms': user_rooms,
            'create_form': CreateRoomForm(),  # 傳遞創建表單
            'join_form': JoinRoomForm(),      # 傳遞加入表單
            'current_room_id': current_room_id,
        }
        return render(request, 'rooms/room_list.html', context)

class CreateRoomView(LoginRequiredMixin, FormView):
    """處理創建新房號"""
    template_name = 'rooms/room_list.html' # 重用列表頁面
    form_class = CreateRoomForm
    success_url = reverse_lazy('rooms:list') # 成功後導回列表

    def form_valid(self, form):
        room = form.save(user=self.request.user) # 儲存並將當前用戶設為成員和管理員
        # 自動設定為當前房間
        self.request.session['current_room_id'] = room.id
        return super().form_valid(form)

    # 處理表單驗證失敗時，需將其他表單和房間列表傳回
    def form_invalid(self, form):
        return RoomListView.as_view()(self.request, create_form=form) # 重新渲染列表頁面，但包含錯誤

class JoinRoomView(LoginRequiredMixin, FormView):
    """處理加入現有房號"""
    template_name = 'rooms/room_list.html' # 重用列表頁面
    form_class = JoinRoomForm
    success_url = reverse_lazy('rooms:list')

    def form_valid(self, form):
        room = form.cleaned_data['room']
        
        # 檢查用戶是否已在房間內
        if self.request.user in room.members.all():
            form.add_error(None, "您已是該房號的成員。")
            return self.form_invalid(form)

        room.members.add(self.request.user) # 將用戶加入房間
        self.request.session['current_room_id'] = room.id # 自動設定為當前房間
        return super().form_valid(form)

    def form_invalid(self, form):
        return RoomListView.as_view()(self.request, join_form=form) # 重新渲染列表頁面，但包含錯誤


# 這裡需要一個輔助函數來獲取當前房間
def get_current_room(request):
    current_room_id = request.session.get('current_room_id') 
    if current_room_id:
        try:
            # 這裡我們只檢查房間是否存在，因為我們只在 RoomMembersView 中使用
            return Room.objects.get(id=current_room_id)
        except Room.DoesNotExist:
            return None
    return None

class RoomMembersView(LoginRequiredMixin, View):
    """用於顯示當前房間所有成員的清單"""
    template_name = 'rooms/room_members.html' # 需要創建這個模板

    def get(self, request):
        room = get_current_room(request)
        
        if not room:
            # 如果用戶沒有選擇房間，導向房間列表/選擇頁面
            return redirect(reverse('rooms:list'))

        # 獲取該房間的所有成員
        members = room.members.all()

        context = {
            'room': room,
            'members': members,
        }
        return render(request, self.template_name, context)