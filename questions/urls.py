from django.urls import path
from . import views

app_name = 'questions'

urlpatterns = [
    path('', views.index, name='index'),
    path('hot/', views.hot, name='hot'),
    path('tag/<str:tag_name>/', views.tag_view, name='tag'),
    path('question/<int:question_id>/', views.question_detail, name='question_detail'),
    path('ask/', views.ask, name='ask'),
    path('vote/question/', views.vote_question, name='vote_question'),
    path('vote/answer/', views.vote_answer, name='vote_answer'),
    path('mark-correct/', views.mark_correct, name='mark_correct'),
]
