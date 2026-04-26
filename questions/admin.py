from django.contrib import admin
from .models import Answer, AnswerLike, Question, QuestionLike, Tag


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    raw_id_fields = ('author',)
    fields = ('author', 'text', 'is_correct', 'rating')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'rating', 'created_at')
    search_fields = ('title', 'text', 'author__username')
    list_filter = ('created_at', 'tags')
    raw_id_fields = ('author',)
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'author', 'is_correct', 'rating', 'created_at')
    search_fields = ('text', 'author__username', 'question__title')
    list_filter = ('is_correct', 'created_at')
    raw_id_fields = ('author', 'question')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'value')
    raw_id_fields = ('user', 'question')


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'answer', 'value')
    raw_id_fields = ('user', 'answer')