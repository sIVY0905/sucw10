from django.db import models
from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Q

class ChoreManager(models.Manager):
    """
    自定義家務管理器：
    - 狀態判斷（今天 / 指定日期）
    - 週期推算
    - 清單 / 月曆 / 統計 共用邏輯
    """

    # =========================
    # 基礎：應完成日
    # =========================
    def get_due_date(self, chore):
        if not chore.last_completed:
            return date.today()
        return chore.last_completed + timedelta(days=chore.frequency_days)

    # =========================
    # 狀態（今天）
    # =========================
    def get_status(self, chore):
        today = date.today()
        due_date = self.get_due_date(chore)  # 取得理論應完成日

        # 1. 檢查今天是否已完成
        if chore.records.filter(completed_on__date=today).exists():
            return 'Done'

        # 2. 比較「應完成日」與「今天」
        if due_date < today:
            return 'Red'    # 應完成日已過 -> 積欠
        elif due_date == today:
            return 'Green'  # 今天剛好到期 -> 今日事項
        else:
            return 'Grey'   # 未來才到期 -> 尚未開始
    # =========================
    # 週期產生器 ⭐ 核心工具
    # =========================
    def iter_chore_cycles(self, chore, start, end):
        """
        產生 chore 在 [start, end) 區間內的所有理論到期日
        - 會往前回推，確保不漏掉 start 附近的週期
        - 不考慮完成狀態 / 權限
        """
        freq = chore.frequency_days

        # 沒有頻率就不產生
        if not freq or freq <= 0:
            return

        # 找「基準日」：最後完成日 + 週期
        if chore.last_completed:
            base_due = chore.last_completed + timedelta(days=freq)
        else:
            base_due = start

        # ⭐ 關鍵：往前回推到 start 之前最近的一次
        cur = base_due
        while cur - timedelta(days=freq) >= start:
            cur -= timedelta(days=freq)

        # 正向產生
        while cur < end:
            yield cur
            cur += timedelta(days=freq)

    def get_my_todos(self, room, user):
        """獲取該用戶今天該做的，以及積欠的事項"""
        today = date.today()
        # 1. 取得所有可能相關的家事
        chores = self.filter(room=room).filter(
            Q(type='PUBLIC') | Q(type='PRIVATE', assigned_to=user)
        ).prefetch_related('records')

        today_list = []
        overdue_list = []

        for chore in chores:
            # 核心判斷：今天或積欠的狀態下，是不是輪到我？
            # 注意：對於積欠(Red)，通常視為「目前該負責的人」要清理
            if chore.get_current_duty_user(at_date=today) != user:
                continue

            status = self.get_status(chore)
            
            if status == 'Green':
                today_list.append(chore)
            elif status == 'Red':
                overdue_list.append(chore)
                
        return today_list, overdue_list
    # =========================
    # 狀態（指定日期）⭐ 關鍵新增
    # =========================
    def get_status_by_date(self, chore, target_date):
        """
        給月曆 / 統計 / 任意日期用
        """
        today = date.today()
        
        # 該日期是否已完成
        if chore.records.filter(completed_on__date=target_date).exists():
            return 'Done'
        if chore.last_completed and target_date <= chore.last_completed:
            return 'Done'
        if target_date < today:
            # 過去的格子：如果沒完成，一律顯示紅色積欠
            return 'Red'
        elif target_date == today:
            # 今天的格子：呼叫上面的 get_status
            due_date = self.get_due_date(chore)
            return 'Red' if today > due_date else 'Green'
        else:
            # 未來的格子：顯示灰色預測
            return 'Grey'
    # =========================
    # 清單頁（F-3.1 / F-3.2）
    # =========================
    def get_chore_list_data(self, room):
        chores = (
            self.filter(room=room)
            .prefetch_related('records', 'assigned_to')
            .order_by('type', 'private_area', 'title')
        )

        public_chores = []
        private_by_area = {}
        today = date.today()

        for chore in chores:
            last_record = chore.records.order_by('-completed_on').first()
            last_completed = last_record.completed_on if last_record else None

            days_ago = (
                (today - last_completed.date()).days
                if last_completed else None
            )

            data = {
                'id': chore.id,
                'title': chore.title,
                'frequency': chore.frequency_days,
                'last_completed': last_completed,
                'days_ago': days_ago,
                'status': self.get_status(chore),
                'type': chore.get_type_display(),
                'assigned_members': list(
                    chore.assigned_to.all()
                    .values_list('username', flat=True)
                ),
            }

            if chore.type == 'PUBLIC':
                public_chores.append(data)
            else:
                area = chore.private_area or '未分區'
                private_by_area.setdefault(area, []).append(data)

        return {
            'public': public_chores,
            'private_by_area': private_by_area,
        }

    # =========================
    # 月曆資料（週期預測）⭐
    # =========================
    def format_for_calendar(self, room, user, lookahead_days=60):
        today = date.today()
        start_date = today.replace(day=1)
        end_date = today + timedelta(days=lookahead_days)

        events = []

        chores = (
            self.filter(room=room)
            .filter(
                Q(type='PUBLIC') |
                Q(type='PRIVATE', assigned_to=user)
            )
            .prefetch_related('records')
        )

        for chore in chores:
            freq = chore.frequency_days
            cur_due = self.get_due_date(chore)

            # 回推到月初
            while cur_due - timedelta(days=freq) >= start_date:
                cur_due -= timedelta(days=freq)

            while cur_due <= end_date:
                status = self.get_status_by_date(chore, cur_due)

                if status != 'Done':
                    events.append({
                        'date': cur_due.isoformat(),
                        'status': status,
                        'title': chore.title,
                        'is_public': chore.type == 'PUBLIC',
                    })

                cur_due += timedelta(days=freq)

        return events

    
    # =========================
    # 圓餅圖（F-3.4）
    # =========================
    def get_completion_percentage(self, room):
        chores = self.filter(room=room)
        total = chores.count()

        if total == 0:
            return {
                'percentage': 0,
                'completed': 0,
                'pending': 0,
                'total': 0,
            }

        completed = 0
        for chore in chores:
            status = self.get_status(chore)
            if status in ('Done', 'Grey'):
                completed += 1

        return {
            'percentage': int((completed / total) * 100),
            'completed': completed,
            'pending': total - completed,
            'total': total,
        }
    def get_my_completion_percentage(self, room, user):
        """計算指定用戶在該房號的：個人私人家事 + 全體公共家事"""
        # 查詢條件：(房間內 & 公共) OR (房間內 & 私人 & 負責人是我)
        my_chores = self.filter(
            models.Q(room=room, type='PUBLIC') | 
            models.Q(room=room, type='PRIVATE', assigned_to=user)
        ).distinct()
        
        total = my_chores.count()
        if total == 0:
            return {'percentage': 0, 'completed': 0, 'pending': 0, 'total': 0}

        completed = 0
        for chore in my_chores:
            status = self.get_status(chore)
            # Done 表示今天已完成，Grey 表示還沒到期（視為完成/安全）
            if status in ('Done', 'Grey'):
                completed += 1

        return {
            'percentage': int((completed / total) * 100),
            'completed': completed,
            'pending': total - completed,
            'total': total,
        }