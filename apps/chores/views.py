# apps/chores/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View # <-- 確保 View 類別在頂部
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q # Q 用於複雜查詢
from datetime import timedelta
import json # <-- 確保 json 導入
from django.contrib.auth.decorators import login_required
from datetime import date
# 核心模型導入
from apps.rooms.models import Room 
from .models import Chore, ChoreRecord 
from .forms import ChoreForm 


# ===============================================
# 輔助函數 (統一使用這個版本)
# ===============================================

def get_current_room(request):
    """輔助函數：獲取當前用戶和房號。"""
    current_room_id = request.session.get('current_room_id') 
    try:
        # 假設 Room 模型有一個 members 欄位/關係 (已在 rooms/models.py 修正為 joined_rooms)
        room = Room.objects.get(id=current_room_id, members=request.user) 
        return room
    except (Room.DoesNotExist, TypeError):
        return None

# ===============================================
# F-2.0, F-3.0 家務 Views
# ===============================================

class HomeView(LoginRequiredMixin, View): # <-- 使用 View 確保能 redirect
    """F-2.0 主頁儀表板"""
    def get(self, request):
        self.room = get_current_room(request)
        user = request.user
        if not self.room:
            # F-1.3: 如果沒有房間，導向房間選擇頁面
            return redirect(reverse('rooms:list')) 

        # --- 1. 待辦家務 (F-2.1) ---
        today_chores, overdue_chores = Chore.objects.get_my_todos(self.room, user)
        
        raw_events = Chore.objects.format_for_calendar(self.room, user)
        # overdue_chores = []  
        # due_chores = []      
        calendar_events = []
        for e in raw_events:
            color = {
                "Green": "green",
                "Red": "red",
                "Grey": "grey",
            }.get(e["status"], "grey")

            calendar_events.append({
                "date": e["date"],
                "title": e["title"],
                "color": color,
            })
           
        # 2. 個人統計 (Doughnut 圖) - 確保 Manager 也要同步考慮輪替邏輯
        pie_chart_data = Chore.objects.get_my_completion_percentage(self.room, user)

        # 3. 成員貢獻統計
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        member_stats = ChoreRecord.objects.filter(
            chore__room=self.room,
            completed_on__gte=thirty_days_ago
        ).values('completed_by__username').annotate(
            completed_count=Count('completed_by')
        ).order_by('-completed_count')

        context = {
            'room': self.room,
            'today_chores':today_chores,
            'overdue_chores': overdue_chores,
            'member_stats': member_stats,
            'pie_chart_data': pie_chart_data,
            'calendar_data': calendar_events,
        }
        return render(request, 'chores/home.html', context)
        
class ChoreListView(LoginRequiredMixin, ListView): 
    """F-3.1, F-3.2 家務清單與統計"""
    model = Chore
    template_name = 'chores/chore_list.html'
    context_object_name = 'chores'

    def get_queryset(self):
        # 這個 view 不直接用 queryset
        self.room = get_current_room(self.request)
        return Chore.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = get_current_room(self.request)
        user = self.request.user
        context['room'] = room # 確保導航欄顯示房號

        if not room:
            context['no_room_assigned'] = True
            return context

        # 1. 獲取原始清單數據
        list_data = Chore.objects.get_chore_list_data(room)
        
        # 2. 過濾私人家事：只顯示負責人是「目前登入者」的
        filtered_private = {}
        for area, chore_list in list_data['private_by_area'].items():
            # assigned_members 是在 manager.py 中定義的列表
            my_private = [c for c in chore_list if user.username in c['assigned_members']]
            if my_private:
                filtered_private[area] = my_private
        
        context['public'] = list_data['public']
        context['private_by_area'] = filtered_private

        # 3. 圓餅圖：呼叫新的個人統計方法
        context['pie_chart_data'] = Chore.objects.get_my_completion_percentage(room, user)
        # ========= 3️⃣ 日曆資料（這裡才可以用 self / room） =========
        calendar_data = []
        today = timezone.now().date()
        start = today.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1)

        chores = Chore.objects.filter(room=self.room)

        for chore in chores:
            if not chore.last_completed:
                continue

            due = chore.last_completed + timedelta(days=chore.frequency_days)

            while due < end:
                status = Chore.objects.get_status_by_date(chore, due)

                calendar_data.append({
                    "date": due.isoformat(),
                    "title": chore.title,
                    "status": status  # Green / Red / Grey
                })

                due += timedelta(days=chore.frequency_days)
    
        context["calendar_data_json"] = json.dumps(calendar_data)
        return context


# --- CRUD Views (F-3.3) ---

class ChoreCreateView(LoginRequiredMixin, CreateView):
    model = Chore
    form_class = ChoreForm
    template_name = 'chores/chore_form.html'
    success_url = reverse_lazy('chores:list') 

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['room'] = get_current_room(self.request)
        kwargs['user'] = self.request.user # 傳給 Form 用於鎖定負責人
        return kwargs


    def form_valid(self, form):
        self.room = get_current_room(self.request)
        
        if not self.room:
            form.add_error(None, "您尚未加入房號，無法創建家務。")
            return self.form_invalid(form)

        # 確保 room 和 creator 被正確賦值
        form.instance.room = self.room
        form.instance.creator = self.request.user 
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room'] = get_current_room(self.request) # 確保 Template 能拿到 room 物件
        context['user'] = self.request.user # 傳遞當前用戶給 form
        return context


class ChoreUpdateView(LoginRequiredMixin, UpdateView):
    model = Chore
    form_class = ChoreForm
    template_name = 'chores/chore_form.html'
    success_url = reverse_lazy('chores:list')
    
    def get_queryset(self):
        # 確保只能修改當前房號的家務
        self.room = get_current_room(self.request)
        if not self.room:
             return self.model.objects.none()
        return self.model.objects.filter(room=self.room)
    def get_form_kwargs(self): # 編輯頁也需要限制成員選單
        kwargs = super().get_form_kwargs()
        kwargs['room'] = get_current_room(self.request)
        kwargs['user'] = self.request.user # 傳遞當前用戶給 form
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room'] = get_current_room(self.request)
        return context


class ChoreDeleteView(LoginRequiredMixin, DeleteView):
    model = Chore
    template_name = 'chores/chore_confirm_delete.html'
    success_url = reverse_lazy('chores:list')
    
    def get_queryset(self):
        # 確保只能刪除當前房號的家務
        self.room = get_current_room(self.request)
        if not self.room:
             return self.model.objects.none()
        return self.model.objects.filter(room=self.room)


# --- 家務完成 AJAX 視圖 ---

class ChoreCompleteView(LoginRequiredMixin, View):
    """F-3.4 標記家務完成 (用於 POST 請求)"""
    def post(self, request, pk, *args, **kwargs):
        room = get_current_room(request)
        if not room:
            return JsonResponse({'status': 'error', 'message': '請先選擇房號。'}, status=403)

        chore = get_object_or_404(Chore, pk=pk, room=room)
        user = request.user
        
        # 創建新的完成紀錄
        ChoreRecord.objects.create(
            chore=chore,
            completed_by=user,
            completed_on=timezone.now() # 使用 completed_at 而非 completed_on
        )
        
        # 更新 Chore 的 last_completed 字段為今天
        chore.last_completed = timezone.now().date() # 假設 models.py 使用 last_completed_at
        
        # 這裡需要 Chore 模型有計算 next_due_date 的方法
        # chore.next_due_date = chore.calculate_next_due_date() 
        # 簡化：暫時只更新 last_completed_at
        chore.save()
        
        # 返回成功響應
        return JsonResponse({'status': 'success', 'message': f'家務 "{chore.title}" 已標記為完成，舊有積欠已一併清除。'})

    def http_method_not_allowed(self, request, *args, **kwargs):
        return JsonResponse({'status': 'error', 'message': '僅接受 POST 請求。'}, status=405)

@login_required
def chore_stats_api(request):
    room = get_current_room(request)
    chores = Chore.objects.filter(room=room)

    overdue = today_count = future = completed = 0

    for chore in chores:
        status = Chore.objects.get_status(chore)
        if status == "Red":
            overdue += 1
        elif status == "Green":
            today_count += 1
        elif status == "Grey":
            future += 1

    return JsonResponse({
        "overdue": overdue,
        "today": today_count,
        "future": future,
        "total": chores.count()
    })
