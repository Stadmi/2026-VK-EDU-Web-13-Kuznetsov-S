from django.shortcuts import render
from .utils import paginate


def _make_question(question_id, tag_name=None):
    tags = [tag_name] if tag_name else ['django', 'python', 'web']
    return {
        'id': question_id,
        'title': f'Question title #{question_id}',
        'text': f'This is a placeholder description for question {question_id}.',
        'author': 'Megan Fox',
        'votes': question_id % 5 + 1,
        'answers_count': question_id % 4,
        'tags': tags,
    }


def _make_answer(answer_id):
    return {
        'id': answer_id,
        'author': 'AnswerAuthor',
        'text': f'This is a sample answer number {answer_id}.',
        'votes': answer_id % 3,
    }


def index(request):
    questions = [_make_question(i) for i in range(1, 31)]
    page_obj = paginate(questions, request, per_page=5)
    return render(request, 'questions/index.html', {'page_obj': page_obj})


def hot(request):
    questions = [_make_question(i, tag_name='hot') for i in range(1, 26)]
    page_obj = paginate(questions, request, per_page=5)
    return render(request, 'questions/hot.html', {'page_obj': page_obj})


def tag_view(request, tag_name):
    questions = [_make_question(i, tag_name=tag_name) for i in range(1, 21)]
    page_obj = paginate(questions, request, per_page=5)
    return render(request, 'questions/tag.html', {'page_obj': page_obj, 'tag_name': tag_name})


def question_detail(request, question_id):
    question = _make_question(question_id)
    answers = [_make_answer(i) for i in range(1, 4)]
    return render(request, 'questions/question_detail.html', {'question': question, 'answers': answers})


def ask(request):
    return render(request, 'questions/ask.html')
