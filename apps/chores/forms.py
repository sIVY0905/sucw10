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
        super().__init__(*args, **kwargs)
        
        if room:
            # 限制 assigned_to 選項為當前房號的成員
            self.fields['assigned_to'].queryset = room.members.all()
            
        # 初始時隱藏 private_area 欄位 (前端 JS 需配合處理顯示/隱藏)
        # 預設公共家事不需要 private_area
        if not self.instance or self.instance.type == 'PUBLIC':
            self.fields['private_area'].required = False
             # 移除 widget style，前端用 container 控制
            self.fields['private_area'].widget.attrs.pop('style', None)
             
        # 調整 assigned_to 的標籤，M2M 預設是多選
        self.fields['assigned_to'].help_text = "選擇負責這項家務的所有成員。"
        
        
    def clean(self):
        cleaned_data = super().clean()
        chore_type = cleaned_data.get('type')
        private_area = cleaned_data.get('private_area')

        # 驗證：如果是 PRIVATE 類型，private_area 必須填寫
        if chore_type == 'PRIVATE' and not private_area:
             self.add_error('private_area', "私人/區域家事必須指定一個區域名稱。")
             
        return cleaned_data