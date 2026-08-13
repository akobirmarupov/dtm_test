from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from .models import Rating, RatingHistory, TopicRating, SubjectRating


def calculate_stars(correct_count, incorrect_count):
    total = correct_count + incorrect_count
    if total == 0:
        return 0.0
    
    weighted_correct = correct_count - (incorrect_count * 0.5)
    stars = (weighted_correct / total) * 5.0
    
    # 0 dan 5 gacha chegaralash
    return max(0.0, min(5.0, stars))


def get_period_dates(period):
    """
    Davr uchun boshlang'ich va tugash sanalarini qaytaradi.
    
    Args:
        period: 'daily', 'weekly', 'all_time'
    
    Returns:
        (start_date, end_date) tuple
    """
    today = timezone.now().date()
    
    if period == 'daily':
        return today, today
    
    elif period == 'weekly':
        # Haftaning dushanbasidan yakshanbasigacha
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        return week_start, week_end
    
    elif period == 'all_time':
        # Eng qadimgi vaqtdan hozirgi kunigacha
        return today.replace(year=2000), today
    
    return today, today


@transaction.atomic
def update_or_create_rating(user, test_session, correct_count, incorrect_count):
    """
    Talabaning reytingini yangilash yoki yaratish.
    
    Args:
        user: User object
        test_session: TestSession object
        correct_count: To'g'ri javoblar soni
        incorrect_count: Noto'g'ri javoblar soni
    """
    
    # Reytingni barcha davrlarda yangilash
    for period in ['daily', 'weekly', 'all_time']:
        start_date, end_date = get_period_dates(period)
        
        rating, created = Rating.objects.get_or_create(
            user=user,
            period=period,
            period_start_date=start_date,
            period_end_date=end_date,
            defaults={
                'tests_completed': 0,
                'correct_answers': 0,
                'incorrect_answers': 0,
                'stars': 0.0,
            }
        )
        
        # Oldingi statsitika
        old_stars = rating.stars
        old_rank = rating.rank
        
        # Yangi statistika
        rating.tests_completed += 1
        rating.correct_answers += correct_count
        rating.incorrect_answers += incorrect_count
        
        # Yulduzlarni hisoblash
        new_stars = calculate_stars(rating.correct_answers, rating.incorrect_answers)
        rating.stars = new_stars
        
        rating.save()

        # Shu davrdagi o'rnini (rank) hisoblab qo'yamiz — bo'lmasa rank doim None bo'lib qoladi
        better_count = Rating.objects.filter(
            period=period, period_start_date=start_date, period_end_date=end_date,
            stars__gt=rating.stars,
        ).count()
        rating.rank = better_count + 1
        rating.save(update_fields=['rank'])

        # Reyting tarixi yaratish
        if old_stars != new_stars:
            RatingHistory.objects.create(
                user=user,
                rating=rating,
                previous_stars=old_stars,
                new_stars=new_stars,
                stars_change=new_stars - old_stars,
                previous_rank=old_rank,
                new_rank=rating.rank,
                test_session=test_session,
                reason=f'{correct_count} to\'g\'ri + {incorrect_count} notog\'ri = {new_stars:.1f} ⭐',
                period=period,
            )


@transaction.atomic
def update_topic_rating(user, topic, correct_count, incorrect_count):
    """
    Mavzu bo'yicha reytingni yangilash.
    """
    topic_rating, created = TopicRating.objects.get_or_create(
        user=user,
        topic=topic,
        defaults={
            'tests_completed': 0,
            'correct_answers': 0,
            'incorrect_answers': 0,
            'stars': 0.0,
        }
    )
    
    # Statistika yangilash
    topic_rating.tests_completed += 1
    topic_rating.correct_answers += correct_count
    topic_rating.incorrect_answers += incorrect_count
    
    # Yulduzlarni hisoblash
    topic_rating.stars = calculate_stars(
        topic_rating.correct_answers,
        topic_rating.incorrect_answers
    )
    
    topic_rating.save()
    return topic_rating


@transaction.atomic
def update_subject_rating(user, subject, correct_count, incorrect_count):
    """
    Fan bo'yicha reytingni yangilash.
    """
    subject_rating, created = SubjectRating.objects.get_or_create(
        user=user,
        subject=subject,
        defaults={
            'tests_completed': 0,
            'correct_answers': 0,
            'incorrect_answers': 0,
            'stars': 0.0,
        }
    )
    
    # Statistika yangilash
    subject_rating.tests_completed += 1
    subject_rating.correct_answers += correct_count
    subject_rating.incorrect_answers += incorrect_count
    
    # Yulduzlarni hisoblash
    subject_rating.stars = calculate_stars(
        subject_rating.correct_answers,
        subject_rating.incorrect_answers
    )
    
    subject_rating.save()
    return subject_rating


def update_ratings_for_test_result(test_result):
    """
    TestResult yaratilganda barcha reytinglarni yangilash.
    
    Bu funktisyon TestResult signal'dan chaqiriladi.
    
    Args:
        test_result: TestResult object
    """
    user = test_result.session.user
    test_session = test_result.session
    correct_count = test_result.correct_count
    incorrect_count = test_result.incorrect_count
    subject = test_session.subject
    
    # Umumiy reyting yangilash (daily, weekly, all_time)
    update_or_create_rating(
        user=user,
        test_session=test_session,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
    )
    
    # Fan bo'yicha reyting yangilash
    update_subject_rating(
        user=user,
        subject=subject,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
    )
    
    # Mavzu bo'yicha reyting yangilash
    # TestSession'dagi barcha Answer'lardan topic larni olib, har biri uchun yangilash
    from testengine.models import Answer
    from catalog.models import Topic
    
    answers = Answer.objects.filter(session=test_session)
    topics_covered = set()
    
    for answer in answers:
        topic = answer.question.topic
        if topic.id not in topics_covered:
            topics_covered.add(topic.id)
            
            # Mavzudagi to'g'ri/notog'ri javoblar
            topic_answers = answers.filter(question__topic=topic)
            topic_correct = topic_answers.filter(is_correct=True).count()
            topic_incorrect = topic_answers.filter(is_correct=False).count()
            
            update_topic_rating(
                user=user,
                topic=topic,
                correct_count=topic_correct,
                incorrect_count=topic_incorrect,
            )
    
    return True