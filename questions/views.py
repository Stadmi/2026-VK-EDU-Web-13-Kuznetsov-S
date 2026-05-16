import json
import time

import jwt
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import AnswerForm, MarkCorrectForm, QuestionForm, VoteForm
from .models import Answer, AnswerLike, Question, QuestionLike
from .tasks import notify_new_answer, publish_new_answer
from .utils import paginate

ANSWERS_PER_PAGE = 10


def _centrifugo_token(user_id):
    return jwt.encode(
        {'sub': str(user_id), 'exp': int(time.time()) + 3600},
        settings.CENTRIFUGO_TOKEN_SECRET,
        algorithm='HS256',
    )


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
            try:
                notify_new_answer.delay(answer.pk)
                publish_new_answer.delay(answer.pk)
            except Exception:
                pass
            page = _answer_page_for(question, answer.pk)
            return redirect(f"{question.get_absolute_url()}?page={page}#answer-{answer.pk}")

    page_obj = paginate(answers_qs, request, per_page=ANSWERS_PER_PAGE)

    user_question_vote = 0
    user_answer_votes = {}
    if request.user.is_authenticated:
        qlike = QuestionLike.objects.filter(question=question, user=request.user).first()
        user_question_vote = qlike.value if qlike else 0

        answer_ids = [a.id for a in page_obj.object_list]
        alikes = AnswerLike.objects.filter(answer_id__in=answer_ids, user=request.user)
        user_answer_votes = {al.answer_id: al.value for al in alikes}

    centrifugo_token = ''
    if request.user.is_authenticated:
        centrifugo_token = _centrifugo_token(request.user.pk)

    return render(
        request,
        'questions/question_detail.html',
        {
            'question': question,
            'page_obj': page_obj,
            'answer_form': answer_form,
            'user_question_vote': user_question_vote,
            'user_answer_votes': user_answer_votes,
            'centrifugo_token': centrifugo_token,
            'centrifugo_ws_url': settings.CENTRIFUGO_WS_URL,
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


def search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})

    search_query = SearchQuery(q, config='russian')
    search_vector = (
        SearchVector('title', weight='A', config='russian') +
        SearchVector('text', weight='B', config='russian')
    )
    questions = (
        Question.objects
        .annotate(rank=SearchRank(search_vector, search_query))
        .filter(rank__gt=0.01)
        .order_by('-rank')
        .values('id', 'title')[:10]
    )
    results = [
        {'id': row['id'], 'title': row['title'], 'url': f'/question/{row["id"]}/'}
        for row in questions
    ]
    return JsonResponse({'results': results})


def _parse_json_body(request):
    try:
        return json.loads(request.body), None
    except (json.JSONDecodeError, ValueError):
        return None, JsonResponse({'error': 'Неверный формат JSON.'}, status=400)


def vote_question(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {'error': 'Требуется авторизация.', 'redirect': reverse('core:login')},
            status=403,
        )
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается.'}, status=405)

    data, err = _parse_json_body(request)
    if err:
        return err

    form = VoteForm(data)
    if not form.is_valid():
        return JsonResponse({'error': form.errors}, status=400)

    question_id = form.cleaned_data['id']
    value = form.cleaned_data['value']

    try:
        with transaction.atomic():
            question = Question.objects.select_for_update().get(pk=question_id)
            existing = QuestionLike.objects.filter(user=request.user, question=question).first()

            if existing:
                if existing.value == value:
                    question.rating -= existing.value
                    question.save(update_fields=['rating'])
                    existing.delete()
                    user_vote = 0
                else:
                    question.rating += value - existing.value
                    question.save(update_fields=['rating'])
                    existing.value = value
                    existing.save(update_fields=['value'])
                    user_vote = value
            else:
                QuestionLike.objects.create(user=request.user, question=question, value=value)
                question.rating += value
                question.save(update_fields=['rating'])
                user_vote = value
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Вопрос не найден.'}, status=404)

    return JsonResponse({'rating': question.rating, 'user_vote': user_vote})


def vote_answer(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {'error': 'Требуется авторизация.', 'redirect': reverse('core:login')},
            status=403,
        )
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается.'}, status=405)

    data, err = _parse_json_body(request)
    if err:
        return err

    form = VoteForm(data)
    if not form.is_valid():
        return JsonResponse({'error': form.errors}, status=400)

    answer_id = form.cleaned_data['id']
    value = form.cleaned_data['value']

    try:
        with transaction.atomic():
            answer = Answer.objects.select_for_update().get(pk=answer_id)
            existing = AnswerLike.objects.filter(user=request.user, answer=answer).first()

            if existing:
                if existing.value == value:
                    answer.rating -= existing.value
                    answer.save(update_fields=['rating'])
                    existing.delete()
                    user_vote = 0
                else:
                    answer.rating += value - existing.value
                    answer.save(update_fields=['rating'])
                    existing.value = value
                    existing.save(update_fields=['value'])
                    user_vote = value
            else:
                AnswerLike.objects.create(user=request.user, answer=answer, value=value)
                answer.rating += value
                answer.save(update_fields=['rating'])
                user_vote = value
    except Answer.DoesNotExist:
        return JsonResponse({'error': 'Ответ не найден.'}, status=404)

    return JsonResponse({'rating': answer.rating, 'user_vote': user_vote})


def mark_correct(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {'error': 'Требуется авторизация.', 'redirect': reverse('core:login')},
            status=403,
        )
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается.'}, status=405)

    data, err = _parse_json_body(request)
    if err:
        return err

    form = MarkCorrectForm(data)
    if not form.is_valid():
        return JsonResponse({'error': form.errors}, status=400)

    answer_id = form.cleaned_data['answer_id']

    try:
        answer = Answer.objects.select_related('question__author').get(pk=answer_id)
    except Answer.DoesNotExist:
        return JsonResponse({'error': 'Ответ не найден.'}, status=404)

    if answer.question.author_id != request.user.pk:
        return JsonResponse({'error': 'Только автор вопроса может выбрать правильный ответ.'}, status=403)

    with transaction.atomic():
        new_state = not answer.is_correct
        Answer.objects.filter(question=answer.question).update(is_correct=False)
        if new_state:
            answer.is_correct = True
            answer.save(update_fields=['is_correct'])

    return JsonResponse({'answer_id': answer.pk, 'is_correct': new_state})
