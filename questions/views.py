from django.shortcuts import get_object_or_404, render

from .models import Question
from .utils import paginate


def index(request):
    questions = Question.objects.new()
    page_obj = paginate(questions, request, per_page=10)
    return render(request, 'questions/index.html', {'page_obj': page_obj})


def hot(request):
    questions = Question.objects.hot()
    page_obj = paginate(questions, request, per_page=10)
    return render(request, 'questions/hot.html', {'page_obj': page_obj})


def tag_view(request, tag_name):
    questions = Question.objects.by_tag(tag_name)
    page_obj = paginate(questions, request, per_page=10)
    return render(request, 'questions/tag.html', {'page_obj': page_obj, 'tag_name': tag_name})


def question_detail(request, question_id):
    question = get_object_or_404(
        Question.objects.select_related('author', 'author__profile').prefetch_related('tags'),
        pk=question_id
    )
    answers = question.answers.select_related('author', 'author__profile').order_by('-is_correct', '-rating')
    page_obj = paginate(answers, request, per_page=10)
    return render(request, 'questions/question_detail.html', {
        'question': question,
        'page_obj': page_obj,
    })


def ask(request):
    return render(request, 'questions/ask.html')