from django import forms
from django.utils import timezone

from .models import Post, Comment, User


class PostForm(forms.ModelForm):
    """Форма публикации."""

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        # Установка текущей даты и времени как начального значения для поля pub_date
        self.fields['pub_date'].initial = timezone.now()

    class Meta:
        model = Post
        fields = ('title', 'text', 'image', 'location', 'category', 'pub_date')
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']


class EditCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']


class DeleteCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = []


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
