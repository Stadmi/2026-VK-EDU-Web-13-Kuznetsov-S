from django import forms
from django.core.exceptions import ValidationError

from .models import Answer, Question, Tag


class QuestionForm(forms.ModelForm):
    tags = forms.CharField(
        label='Теги',
        required=False,
        help_text='Укажите теги через запятую, например: python, django, web',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Question
        fields = ('title', 'text')
        labels = {
            'title': 'Название',
            'text': 'Текст',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Заголовок вопроса'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Опишите вопрос'}),
        }

    def clean_tags(self):
        raw_tags = self.cleaned_data.get('tags', '')
        tags = []
        for tag in raw_tags.split(','):
            tag = tag.strip().lower()
            if tag and tag not in tags:
                tags.append(tag)
        return tags

    def save(self, user, commit=True):
        question = super().save(commit=False)
        question.author = user
        if commit:
            question.save()
            tags = []
            for tag_name in self.cleaned_data.get('tags', []):
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                tags.append(tag)
            question.tags.set(tags)
        return question


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ('text',)
        labels = {
            'text': 'Ответ',
        }
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Напишите ответ'}),
        }

    def save(self, user, question, commit=True):
        answer = super().save(commit=False)
        answer.author = user
        answer.question = question
        if commit:
            answer.save()
        return answer


class VoteForm(forms.Form):
    id = forms.IntegerField()
    value = forms.IntegerField()

    def clean_value(self):
        value = self.cleaned_data.get('value')
        if value not in (1, -1):
            raise ValidationError('Допустимые значения: 1 (лайк) или -1 (дизлайк).')
        return value


class MarkCorrectForm(forms.Form):
    answer_id = forms.IntegerField()