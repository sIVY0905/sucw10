from django.db import models
from datetime import date, timedelta
from django.utils import timezone


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
        """
        保留原 API：只算「今天」
        """
        return self.get_status_by_date(chore, date.today())

    # =========================
    # 狀態（指定日期）⭐ 關鍵新增
    # =========================
    def get_status_by_date(self, chore, target_date):
        """
        給月曆 / 統計 / 任意日期用
        """
        due_date = self.get_due_date(chore)

        # 是否在 target_date 當天完成
        completed = chore.records.filter(
            completed_on__date=target_date
        ).exists()

        if completed:
            return 'Done'

        days_diff = (target_date - due_date).days

        if days_diff < 0:
            return 'Grey'     # 未來
        if days_diff <= 1:
            return 'Green'    # 今天 or 逾期 1 天
        return 'Red'          # 逾期 2 天以上

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
    def format_for_calendar(self, room, lookahead_days=60):
        """
        直接從 Chore 推算，不依賴 dashboard_data（更穩定）
        """
        today = date.today()
        end_date = today + timedelta(days=lookahead_days)

        events = []

        chores = self.filter(room=room).prefetch_related('records')

        for chore in chores:
            cur_due = self.get_due_date(chore)

            while cur_due <= end_date:
                status = self.get_status_by_date(chore, cur_due)

                events.append({
                    'date': cur_due.isoformat(),
                    'status': status,
                    'title': chore.title,
                    'is_public': chore.type == 'PUBLIC',
                })

                cur_due += timedelta(days=chore.frequency_days)

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
