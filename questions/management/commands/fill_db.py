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

        users = self._create_users(ratio)
        self._create_profiles(users)
        tags = self._create_tags(ratio)
        questions = self._create_questions(ratio, users, tags)
        answers = self._create_answers(ratio, users, questions)
        self._create_question_likes(ratio, users, questions)
        self._create_answer_likes(ratio, users, answers)

        self.stdout.write(self.style.SUCCESS(f'Готово! ratio={ratio}'))

    def _create_users(self, ratio):
        self.stdout.write('Создаю пользователей...')
        users = [
            User(
                username=f'user_{i}_{fake.unique.user_name()}'[:150],
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
            for i in range(ratio)
        ]
        User.objects.bulk_create(users, ignore_conflicts=True)
        return list(User.objects.all())

    def _create_profiles(self, users):
        self.stdout.write('Создаю профили...')
        existing = set(Profile.objects.values_list('user_id', flat=True))
        profiles = [Profile(user=u) for u in users if u.id not in existing]
        Profile.objects.bulk_create(profiles, ignore_conflicts=True)

    def _create_tags(self, ratio):
        self.stdout.write('Создаю теги...')
        tags = [Tag(name=f'tag_{i}_{fake_en.word()}'[:50]) for i in range(ratio)]
        Tag.objects.bulk_create(tags, ignore_conflicts=True)
        return list(Tag.objects.all())

    def _create_questions(self, ratio, users, tags):
        self.stdout.write('Создаю вопросы...')
        questions = [
            Question(
                author=random.choice(users),
                title=fake.sentence(nb_words=6)[:255],
                text=fake.paragraph(nb_sentences=5),
                rating=random.randint(-10, 100),
            )
            for _ in range(ratio * 10)
        ]
        Question.objects.bulk_create(questions)
        questions = list(Question.objects.all())

        self.stdout.write('Привязываю теги к вопросам...')
        QT = Question.tags.through
        used = set()
        qt_objs = []
        for q in questions:
            for tag in random.sample(tags, k=random.randint(1, 3)):
                key = (q.id, tag.id)
                if key not in used:
                    used.add(key)
                    qt_objs.append(QT(question_id=q.id, tag_id=tag.id))
        QT.objects.bulk_create(qt_objs, ignore_conflicts=True)

        return questions

    def _create_answers(self, ratio, users, questions):
        self.stdout.write('Создаю ответы...')
        answers = [
            Answer(
                author=random.choice(users),
                question=random.choice(questions),
                text=fake.paragraph(nb_sentences=3),
                is_correct=random.random() < 0.1,
                rating=random.randint(-5, 50),
            )
            for _ in range(ratio * 100)
        ]
        Answer.objects.bulk_create(answers)
        return list(Answer.objects.all())

    def _create_question_likes(self, ratio, users, questions):
        self.stdout.write('Создаю лайки вопросов...')
        used = set()
        objs = []
        for _ in range(ratio * 200 // 2):
            u = random.choice(users)
            q = random.choice(questions)
            if (u.id, q.id) not in used:
                used.add((u.id, q.id))
                objs.append(QuestionLike(user=u, question=q, value=random.choice([1, -1])))
        QuestionLike.objects.bulk_create(objs, ignore_conflicts=True)

    def _create_answer_likes(self, ratio, users, answers):
        self.stdout.write('Создаю лайки ответов...')
        used = set()
        objs = []
        for _ in range(ratio * 200 // 2):
            u = random.choice(users)
            a = random.choice(answers)
            if (u.id, a.id) not in used:
                used.add((u.id, a.id))
                objs.append(AnswerLike(user=u, answer=a, value=random.choice([1, -1])))
        AnswerLike.objects.bulk_create(objs, ignore_conflicts=True)
