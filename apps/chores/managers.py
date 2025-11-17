from django.db import models
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Count

class ChoreManager(models.Manager):
    """
    自定義家務管理器，專門處理頻率計算、狀態判斷和儀表板數據準備。
    """
    
    def get_due_date(self, chore):
        """計算下一個應完成日期 (Next Due Date)"""
        if not chore.last_completed:
            # 首次計算：從今天算起
            return date.today()
        
        # 應完成日期 = 上次完成日期 + 頻率
        return chore.last_completed + timedelta(days=chore.frequency_days)

    def get_status(self, chore):
        """
        判斷家務的紅綠燈狀態標記。
        - Green: 當天應完成 或 首次逾期 (昨天應完成)
        - Red: 累積第二次通知 (逾期兩天或以上)
        - Grey: 未來的預訂家事
        """
        today = date.today()
        due_date = self.get_due_date(chore)
        
        days_diff = (today - due_date).days
        # 1. 未來的預訂家事 (Grey)
        if days_diff < 0:
            return 'Grey'
        
        # 2. 當天應完成 (Green)
        if days_diff == 0:
            return 'Green'
            
        # 3. 逾期判斷 (Red / Green)
        if days_diff >= 2:
            # 逾期兩天或以上 (今天 - 應完成日期 >= 2) -> 紅色標記 (累積第二次逾期)
            return 'Red'
        elif days_diff == 1:
            # 逾期一天 (今天 - 應完成日期 = 1) -> 綠色標記 (首次通知/寬限期)
            # 這裡的 Green 標記與 F-2.3 的描述 (當天綠色) 略有出入，但用於寬限期是合理的設計。
            # 如果要嚴格按照 F-2.3，這裡應作為一個單獨的逾期狀態 (黃色) 處理，但程式碼中暫時歸類為 Green。
            return 'Green'
        
        # 如果 due_date 遠早於今天，應該仍然是 Red (已包含在 days_diff >= 2)
        # 預設情況（理論上不應發生）
        return 'Grey'


    def get_home_dashboard_data(self, room):
        """
        為主頁儀表板準備所有家事清單數據。
        """
        today = date.today()
        
        # 僅查詢當前房號的家事，並預載入 Records 關係，減少資料庫查詢
        chores = self.filter(room=room).prefetch_related('records')
        
        dashboard_data = []
        
        for chore in chores:
            status = self.get_status(chore)
            due_date = self.get_due_date(chore)
            
            # 判斷是否已在今天完成
            # 使用 reverse relation: chore.records.all().filter(...)
            is_completed_today = chore.records.filter(completed_on__date=today).exists()
            
            data = {
                'id': chore.id,
                'title': chore.title,
                'type': chore.get_type_display(), # 假設 Chore.type 有 choices
                'status': status,
                'due_date': due_date,
                'is_completed_today': is_completed_today,
                # 邏輯上的積欠：狀態為 Red 或狀態為 Green 但 due_date 小於今天 (即逾期 1 天)
                'is_overdue': status == 'Red' or (status == 'Green' and due_date < today),
            }
            dashboard_data.append(data)
            
        return dashboard_data
        
    def format_for_calendar(self, dashboard_data, lookahead_days=60):
        """
        將儀表板數據格式化為日曆所需的 JSON 列表，並生成未來預訂 (Grey) 的事件。
        """
        calendar_events = []
        today = date.today()
        
        # 1. 處理當前狀態為 Green/Red/Grey 的家事 (當天或逾期)
        for data in dashboard_data:
            if not data['is_completed_today']:
                calendar_events.append({
                    'date': data['due_date'].isoformat(),
                    'status': data['status'],
                    'title': data['title'],
                    'is_public': data['type'] == '公共家事',
                })
        
        # 2. 預測未來的預訂家事 (Grey)
        chores_to_predict = self.filter(id__in=[c['id'] for c in dashboard_data]) # 獲取所有 Chore 實例
        end_date = today + timedelta(days=lookahead_days)
        
        for chore in chores_to_predict:
            if chore.frequency_days > 0:
                current_due = self.get_due_date(chore)
                
                # 從當前應完成日期開始，每隔 frequency_days 產生一個未來事件
                while current_due <= end_date:
                    # 只加入未來的事件
                    if current_due > today:
                        calendar_events.append({
                            'date': current_due.isoformat(),
                            'status': 'Grey',
                            'title': chore.title,
                            'is_public': chore.type == 'PUBLIC', # 假設 PUBLIC 是類型值
                        })
                    current_due += timedelta(days=chore.frequency_days)
                    
        return calendar_events

    def get_today_duty_roster(self, room):
        """
        獲取今日值日生表資訊。
        (此處僅為 placeholder 邏輯，實際輪值需要更複雜的排程演算法)
        """
        # 簡單示例：假設公共家事按成員 ID 輪流
        roster = []
        today = date.today()
        public_chores = self.filter(room=room, type='PUBLIC')
        members = list(room.members.all())
        
        if not members:
            return []

        for i, chore in enumerate(public_chores):
            # 簡單輪值邏輯：根據家事的索引和當前日期，輪流分配
            member_index = (today.timetuple().tm_yday + i) % len(members)
            roster.append({
                'chore': chore.title,
                'duty_member': members[member_index].username
            })
        return roster

def get_chore_list_data(self, room):
    """
    獲取家務清單並按類型、區域分組，準備上次紀錄數據 (F-3.1, F-3.2)。
    """
    chores = self.filter(room=room).prefetch_related('records').order_by('type', 'private_area', 'title')
    
    public_chores = []
    private_chores_by_area = {}
    
    for chore in chores:
        # 獲取上次完成紀錄 (F-3.1, F-3.6)
        last_record = chore.records.order_by('-completed_on').first()
        last_completed_date = last_record.completed_on.date() if last_record else None
        
        days_ago = None
        if last_completed_date:
            days_ago = (date.today() - last_completed_date).days

        data = {
            'id': chore.id,
            'title': chore.title,
            'frequency': chore.frequency_days,
            'last_completed': last_completed_date,
            'days_ago': days_ago,
            'assigned_members': list(chore.assigned_to.all().values_list('username', flat=True)),
            # 這裡可以加入 get_status(chore) 來顯示紅綠燈
        }
        
        if chore.type == 'PUBLIC':
            public_chores.append(data)
        elif chore.type == 'PRIVATE':
            area = chore.private_area if chore.private_area else '未分區'
            if area not in private_chores_by_area:
                private_chores_by_area[area] = []
            private_chores_by_area[area].append(data)
            
    return {
        'public': public_chores,
        'private_by_area': private_chores_by_area,
    }

def get_completion_percentage(self, room):
    """
    計算家務總體完成占比 (F-3.4)，基於當前狀態。
    """
    all_chores = self.filter(room=room)
    total_count = all_chores.count()
    
    if total_count == 0:
        return {'percentage': 0, 'completed': 0, 'total': 0}

    completed_count = 0
    
    for chore in all_chores:
        status = self.get_status(chore) # 沿用 HomeView 的狀態邏輯
        
        # 狀態為 Grey (未來預訂) 或 今天已完成，視為已完成
        is_completed_today = chore.records.filter(completed_on__date=date.today()).exists()
        
        if status == 'Grey' or is_completed_today:
            completed_count += 1
        
    percentage = int((completed_count / total_count) * 100)
    
    return {
        'percentage': percentage,
        'completed': completed_count,
        'pending': total_count - completed_count, # 待辦/積欠數
        'total': total_count,
    }