from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import AnswerForm, QuestionForm
from .models import Question
from .utils import paginate

ANSWERS_PER_PAGE = 10


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


def _answer_page_for(question, answer_id):
    answer_ids = list(
        question.answers.order_by('-is_correct', '-rating', '-created_at', '-id').values_list('id', flat=True)
    )
    try:
        index = answer_ids.index(answer_id)
    except ValueError:
        return 1
    return index // ANSWERS_PER_PAGE + 1


def question_detail(request, question_id):
    question = get_object_or_404(
        Question.objects.select_related('author', 'author__profile').prefetch_related('tags'),
        pk=question_id,
    )
    answers_qs = question.answers.select_related('author', 'author__profile').order_by(
        '-is_correct', '-rating', '-created_at', '-id'
    )

    answer_form = AnswerForm()
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f"{reverse('core:login')}?next={request.get_full_path()}")

        answer_form = AnswerForm(request.POST)
        if answer_form.is_valid():
            answer = answer_form.save(user=request.user, question=question)
            page = _answer_page_for(question, answer.pk)
            return redirect(f"{question.get_absolute_url()}?page={page}#answer-{answer.pk}")

    page_obj = paginate(answers_qs, request, per_page=ANSWERS_PER_PAGE)
    return render(
        request,
        'questions/question_detail.html',
        {
            'question': question,
            'page_obj': page_obj,
            'answer_form': answer_form,
        },
    )


@login_required(login_url='core:login')
def ask(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(user=request.user)
            return redirect(question.get_absolute_url())
    else:
        form = QuestionForm()

    return render(request, 'questions/ask.html', {'form': form})