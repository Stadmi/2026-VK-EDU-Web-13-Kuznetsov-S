from datetime import timedelta

import requests as http_requests
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Count, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

POPULAR_TAGS_CACHE_KEY = 'sidebar:popular_tags'
BEST_MEMBERS_CACHE_KEY = 'sidebar:best_members'
CACHE_TIMEOUT = 60 * 60  # 1 час


@shared_task
def update_popular_tags_cache():
    from .models import Tag

    three_months_ago = timezone.now() - timedelta(days=90)
    tags = list(
        Tag.objects
        .filter(questions__created_at__gte=three_months_ago)
        .annotate(q_count=Count('questions', distinct=True))
        .order_by('-q_count')
        .values('name', 'q_count')[:10]
    )
    try:
        cache.set(POPULAR_TAGS_CACHE_KEY, tags, CACHE_TIMEOUT)
    except Exception:
        pass
    return tags


@shared_task
def update_best_members_cache():
    from django.contrib.auth.models import User

    one_week_ago = timezone.now() - timedelta(days=7)
    users = list(
        User.objects
        .filter(
            Q(questions__created_at__gte=one_week_ago) |
            Q(answers__created_at__gte=one_week_ago)
        )
        .annotate(
            score=Coalesce(
                Sum('questions__rating',
                    filter=Q(questions__created_at__gte=one_week_ago)),
                Value(0),
            ) + Coalesce(
                Sum('answers__rating',
                    filter=Q(answers__created_at__gte=one_week_ago)),
                Value(0),
            )
        )
        .filter(score__gt=0)
        .order_by('-score')
        .distinct()
        .values('username', 'score')[:10]
    )
    try:
        cache.set(BEST_MEMBERS_CACHE_KEY, users, CACHE_TIMEOUT)
    except Exception:
        pass
    return users


@shared_task
def notify_new_answer(answer_id):
    from .models import Answer

    try:
        answer = Answer.objects.select_related(
            'question__author', 'author'
        ).get(pk=answer_id)
    except Answer.DoesNotExist:
        return

    question = answer.question
    author = question.author

    if not author.email or author.pk == answer.author.pk:
        return

    send_mail(
        subject=f'Новый ответ на ваш вопрос: {question.title}',
        message=(
            f'Здравствуйте, {author.username}!\n\n'
            f'{answer.author.username} ответил на ваш вопрос «{question.title}»:\n\n'
            f'{answer.text}\n\n'
            f'Перейти к вопросу: http://localhost:8000{question.get_absolute_url()}'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[author.email],
        fail_silently=True,
    )


@shared_task
def publish_new_answer(answer_id):
    from .models import Answer

    try:
        answer = Answer.objects.select_related('author', 'question').get(pk=answer_id)
    except Answer.DoesNotExist:
        return

    payload = {
        'channel': f'question:{answer.question_id}',
        'data': {
            'type': 'new_answer',
            'answer_id': answer.pk,
            'author': answer.author.username,
            'text': answer.text,
            'rating': answer.rating,
            'is_correct': answer.is_correct,
        },
    }

    try:
        http_requests.post(
            settings.CENTRIFUGO_API_URL,
            json=payload,
            headers={
                'Authorization': f'apikey {settings.CENTRIFUGO_API_KEY}',
                'Content-Type': 'application/json',
            },
            timeout=5,
        )
    except Exception:
        pass
