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
            # 限制 assigned_to 選項為當前房號的成員 (解決你提到的指派給所有帳號問題)
            self.fields['assigned_to'].queryset = room.members.all()
        
        self.fields['private_area'].required = False
        self.fields['assigned_to'].help_text = "選擇負責這項家務的所有成員。"
        
        
    def clean(self):
        cleaned_data = super().clean()
        chore_type = cleaned_data.get('type')
        private_area = cleaned_data.get('private_area')
        assigned_to = cleaned_data.get('assigned_to')
        
        # 驗證 1：PRIVATE 類型必須填寫區域
        if chore_type == 'PRIVATE' and not private_area:
            self.add_error('private_area', "私人/區域家事必須指定一個區域名稱。")

        # 驗證 2：私人家事限定本人
        if chore_type == 'PRIVATE' and assigned_to and self.user:
            # assigned_to 是多選，如果裡面沒有包含當前用戶，報錯
            if self.user not in assigned_to:
                self.add_error('assigned_to', f"私人家事必須指派給您本人 ({self.user.username})。")
            # 如果選了超過一個人，也報錯
            if len(assigned_to) > 1:
                self.add_error('assigned_to', "私人家事只能指派給單一成員（您本人）。")
                
        return cleaned_data