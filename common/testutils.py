"""Testlar uchun umumiy yordamchilar."""

from django.contrib.auth import get_user_model

from catalog.models import Question, Subject, Topic
from common.models import Role

User = get_user_model()


def make_user(email, role=Role.STUDENT, **extra):
    return User.objects.create_user(email=email, role=role, **extra)


def make_question(subject_name='Matematika', correct='A', topic_name='Algebra', **extra):
    """Fan -> Mavzu -> Savol zanjirini yaratadi va savolni qaytaradi."""
    subject, _ = Subject.objects.get_or_create(name=subject_name)
    topic, _ = Topic.objects.get_or_create(subject=subject, name=topic_name)
    question = Question.objects.create(
        topic=topic,
        text=extra.pop('text', f'{subject_name} savoli'),
        options=extra.pop('options', {'A': '1', 'B': '2', 'C': '3', 'D': '4'}),
        correct_option=correct,
        **extra,
    )
    return question


def make_questions(count, subject_name='Matematika', correct='A', topic_name='Algebra'):
    """Bitta fan ichida `count` ta savol — 15 savolli sessiyalarni sinash uchun."""
    subject, _ = Subject.objects.get_or_create(name=subject_name)
    topic, _ = Topic.objects.get_or_create(subject=subject, name=topic_name)
    return [
        Question.objects.create(
            topic=topic,
            text=f'{subject_name} savoli #{index}',
            options={'A': '1', 'B': '2', 'C': '3', 'D': '4'},
            correct_option=correct,
        )
        for index in range(1, count + 1)
    ]


def make_plan(name, price, duration_days=30, **extra):
    """Tarif rejasi (0 so'm / 50 000 so'm / 70 000 so'm)."""
    from billing.models import Plan
    return Plan.objects.create(
        name=name, price=price, duration_days=duration_days, **extra
    )
