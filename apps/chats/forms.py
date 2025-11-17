from django import forms
from .models import Chat # ***模型名稱變更為 Chat***

class ArticleForm(forms.ModelForm):
    """用於創建和編輯文章 (is_article=True)"""
    class Meta:
        model = Chat 
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': '文章標題', 'class': 'w-full p-3 border rounded-lg focus:ring-purple-500 focus:border-purple-500'}),
            'content': forms.Textarea(attrs={'placeholder': '請輸入文章內容...', 'rows': 10, 'class': 'w-full p-3 border rounded-lg focus:ring-purple-500 focus:border-purple-500'})
        }

class ReplyForm(forms.ModelForm):
    """用於創建留言 (is_article=False)"""
    class Meta:
        model = Chat # ***使用 Chat 模型***
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': '請輸入你的留言...', 'rows': 3})
        }