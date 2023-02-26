from django import forms
from django.contrib.auth import get_user_model

from .models import Post, Comment

user = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Текст поста',
                  'group': 'Группа',
                  'image': 'Изображение'},
        help_texts = {'text': 'Введите текст поста',
                      'group': 'Выберите группу',
                      'image': 'Вставьте картинку'}

    def clean_text(self):
        data = self.cleaned_data['text']
        if data.lower() == '':
            raise forms.ValidationError('Поле обязательно нужно заполнить')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Текст комментария'},
        help_texts = {'text': 'Введите текст комментария'}
