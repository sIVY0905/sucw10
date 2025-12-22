# chores/forms.py (新增)
from django import forms
from .models import Chore
from apps.rooms.models import Room # 確保 Room 已導入

class ChoreForm(forms.ModelForm):
    
    class Meta:
        model = Chore
        fields = ['title', 'type', 'frequency_days', 'last_completed', 'assigned_to', 'private_area']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': '例如：倒垃圾、洗浴室', 'class': 'w-full p-2 border rounded-lg'}),
            'frequency_days': forms.NumberInput(attrs={'min': 1, 'class': 'p-2 border rounded-lg'}),
            'last_completed': forms.DateInput(attrs={'type': 'date', 'class': 'p-2 border rounded-lg'}),
            'private_area': forms.TextInput(attrs={'placeholder': '例如：主臥室、客廳', 'class': 'w-full p-2 border rounded-lg'}),
            'type': forms.Select(attrs={'class': 'p-2 border rounded-lg w-full'}),
            'assigned_to': forms.SelectMultiple(attrs={'class': 'p-2 border rounded-lg w-full'}),
        }
        labels = {
            'title': '家務名稱',
            'type': '家務類型',
            'frequency_days': '頻率 (天)',
            'last_completed': '上次完成日期',
            'assigned_to': '負責成員',
            'private_area': '私人/區域名稱',
        }

    def __init__(self, *args, **kwargs):
        # 彈出 room 參數，用於限制 assigned_to 的選項
        room = kwargs.pop('room', None) 
        user = kwargs.pop('user', None) # 獲取當前用戶用於私人家事過濾
        super().__init__(*args, **kwargs)
        #將 user 存入 instance 變數，這樣 clean 方法才找得到
        self.user = user
        if room:
            # 鎖定選單內容僅限房內成員
            self.fields['assigned_to'].queryset = room.members.all()
        # 如果是新增且類型預設是 PRIVATE，或編輯時是 PRIVATE
        if self.instance.type == 'PRIVATE' or (not self.instance.pk and self.data.get('type') == 'PRIVATE'):
            # 這裡不使用 disabled=True，因為 disabled 的欄位不會在 POST 送出資料
            # 改在 clean 中強制覆蓋，並在 Template 用 CSS 鎖定
            pass
        
    def clean(self):
        cleaned_data = super().clean()
        chore_type = cleaned_data.get('type')
        private_area = cleaned_data.get('private_area')
        # 強制邏輯：如果是私人家事，負責人強行設為當前用戶
        if chore_type == 'PRIVATE':
            if not private_area:
                self.add_error('private_area', "私人家事必須填寫區域。")
            if self.user:
                cleaned_data['assigned_to'] = [self.user]
        return cleaned_data