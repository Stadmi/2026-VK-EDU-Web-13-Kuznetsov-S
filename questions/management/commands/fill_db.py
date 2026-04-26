import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from faker import Faker

from core.models import Profile
from questions.models import Answer, AnswerLike, Question, QuestionLike, Tag

fake = Faker('ru_RU')
fake_en = Faker('en_US')


class Command(BaseCommand):
    help = 'Заполнение базы данных тестовыми данными'

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int, help='Коэффициент заполнения')

    def handle(self, *args, **options):
        ratio = options['ratio']

        # --- Пользователи ---
        self.stdout.write('Создаю пользователей...')
        users = []
        for i in range(ratio):
            users.append(User(
                username=f'user_{i}_{fake.unique.user_name()}'[:150],
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            ))
        User.objects.bulk_create(users, ignore_conflicts=True)
        users = list(User.objects.all())

        # --- Профили ---
        self.stdout.write('Создаю профили...')
        existing = set(Profile.objects.values_list('user_id', flat=True))
        profiles = [Profile(user=u) for u in users if u.id not in existing]
        Profile.objects.bulk_create(profiles, ignore_conflicts=True)

        # --- Теги ---
        self.stdout.write('Создаю теги...')
        tags = []
        for i in range(ratio):
            tags.append(Tag(name=f'tag_{i}_{fake_en.word()}'[:50]))
        Tag.objects.bulk_create(tags, ignore_conflicts=True)
        tags = list(Tag.objects.all())

        # --- Вопросы ---
        self.stdout.write('Создаю вопросы...')
        questions = []
        for _ in range(ratio * 10):
            questions.append(Question(
                author=random.choice(users),
                title=fake.sentence(nb_words=6)[:255],
                text=fake.paragraph(nb_sentences=5),
                rating=random.randint(-10, 100),
            ))
        Question.objects.bulk_create(questions)
        questions = list(Question.objects.all())

        # --- Теги для вопросов (M2M) ---
        self.stdout.write('Привязываю теги к вопросам...')
        QT = Question.tags.through
        qt_objs = []
        used = set()
        for q in questions:
            for tag in random.sample(tags, k=random.randint(1, 3)):
                key = (q.id, tag.id)
                if key not in used:
                    used.add(key)
                    qt_objs.append(QT(question_id=q.id, tag_id=tag.id))
        QT.objects.bulk_create(qt_objs, ignore_conflicts=True)

        # --- Ответы ---
        self.stdout.write('Создаю ответы...')
        answers = []
        for _ in range(ratio * 100):
            answers.append(Answer(
                author=random.choice(users),
                question=random.choice(questions),
                text=fake.paragraph(nb_sentences=3),
                is_correct=random.random() < 0.1,
                rating=random.randint(-5, 50),
            ))
        Answer.objects.bulk_create(answers)
        answers = list(Answer.objects.all())

        # --- Лайки вопросов ---
        self.stdout.write('Создаю лайки вопросов...')
        ql_objs = []
        used_ql = set()
        for _ in range(ratio * 200 // 2):
            u = random.choice(users)
            q = random.choice(questions)
            if (u.id, q.id) not in used_ql:
                used_ql.add((u.id, q.id))
                ql_objs.append(QuestionLike(user=u, question=q, value=random.choice([1, -1])))
        QuestionLike.objects.bulk_create(ql_objs, ignore_conflicts=True)

        # --- Лайки ответов ---
        self.stdout.write('Создаю лайки ответов...')
        al_objs = []
        used_al = set()
        for _ in range(ratio * 200 // 2):
            u = random.choice(users)
            a = random.choice(answers)
            if (u.id, a.id) not in used_al:
                used_al.add((u.id, a.id))
                al_objs.append(AnswerLike(user=u, answer=a, value=random.choice([1, -1])))
        AnswerLike.objects.bulk_create(al_objs, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(f'Готово! ratio={ratio}'))