# apps/rooms/forms.py (新增)
from django import forms
from .models import Room
from django.contrib.auth.hashers import make_password, check_password

class RoomBaseForm(forms.ModelForm):
    """基礎房號表單，定義密碼欄位"""
    password = forms.CharField(widget=forms.PasswordInput, label='房號密碼')
    
    class Meta:
        model = Room
        fields = ['room_number', 'password']
        
class CreateRoomForm(RoomBaseForm):
    """創建新房號的表單"""
    
    def save(self, commit=True, user=None):
        room = super().save(commit=False)
        # 儲存 Hashed 密碼
        room.password = make_password(self.cleaned_data["password"])
        
        if commit:
            room.save()
            if user:
                # 將創建者設為成員，並設為管理員 (假設 creator 同時是 admin)
                room.members.add(user)
                room.creator = user
                room.save() 
        return room

class JoinRoomForm(forms.Form):
    """加入房號的表單，用於驗證密碼"""
    room_number = forms.CharField(max_length=50, label='房號代碼')
    password = forms.CharField(widget=forms.PasswordInput, label='房號密碼')

    def clean(self):
        cleaned_data = super().clean()
        room_number = cleaned_data.get('room_number')
        password = cleaned_data.get('password')

        if room_number and password:
            try:
                room = Room.objects.get(room_number=room_number)
            except Room.DoesNotExist:
                raise forms.ValidationError('該房號不存在，請檢查房號代碼。')

            # 驗證密碼
            if not check_password(password, room.password):
                raise forms.ValidationError('房號密碼錯誤。')
            
            cleaned_data['room'] = room # 將驗證後的 Room 實例加入
        
        return cleaned_data