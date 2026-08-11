# 🔧 RATING SISTEMASINI AVTOMATIK YANGILASH LOGIKASI

**Maqsad:** Talaba test ishlaganda avtomatik reyting yangilash  
**Status:** Ko'rsatma (Implementation qilish kerak)

---

## 📋 KERAK BO'LADIGAN QADAMLAR

### Qadam 1: Signal Yaratish (progress/signals.py)

Test yakunlaganda avtomatik rating yangilash uchun signal yozish kerak:

```python
# progress/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from testengine.models import TestResult, Answer
from rating.models import Rating, RatingHistory, TopicRating, SubjectRating, Leaderboard
from account.models import User


@receiver(post_save, sender=TestResult)
def update_ratings_on_test_completion(sender, instance, created, **kwargs):
    """
    Test yakunida barcha reyting modellarini yangilash.
    
    Qadamlar:
    1. Test natijasindan stars hisoblash
    2. User'ning mavzu reytingini yangilash (TopicRating)
    3. User'ning fan reytingini yangilash (SubjectRating)
    4. User'ning davr reytinglarini yangilash (Rating: daily, weekly, all_time)
    5. Reyting o'zgarsa, RatingHistory yaratish
    6. Leaderboard'ni qayta hisoblash
    """
    
    if not created:
        return  # Faqat yangi TestResult uchun
    
    test_session = instance.session
    user = test_session.user
    subject = test_session.subject
    
    # ===============================================
    # BOSQICH 1: Test natijasindan stars hisoblash
    # ===============================================
    
    total_questions = instance.correct_count + instance.incorrect_count
    if total_questions == 0:
        return
    
    # Formula: (To'g'ri - Noto'g'ri * 0.5) / Jami * 5
    test_stars = (instance.correct_count - instance.incorrect_count * 0.5) / total_questions * 5
    test_stars = max(0, min(5, test_stars))  # 0-5 oraligiga cheklash
    
    # ===============================================
    # BOSQICH 2: Mavzu reytingini yangilash (Topic)
    # ===============================================
    
    topic_rating, _ = TopicRating.objects.get_or_create(
        user=user,
        topic=test_session.subject  # subjects emas, topic bo'lsa buyon xatolik
    )
    
    # Mavzudagi barcha test natijalari
    topic_answers = Answer.objects.filter(
        session__user=user,
        question__topic=test_session.subject
    )
    
    topic_correct = sum(1 for a in topic_answers if a.is_correct)
    topic_incorrect = topic_answers.count() - topic_correct
    topic_tests = Answer.objects.filter(
        session__user=user,
        question__topic=test_session.subject
    ).values_list('session_id', flat=True).distinct().count()
    
    if topic_answers.exists():
        topic_rating.stars = (topic_correct - topic_incorrect * 0.5) / topic_answers.count() * 5
        topic_rating.stars = max(0, min(5, topic_rating.stars))
        topic_rating.tests_completed = topic_tests
        topic_rating.correct_answers = topic_correct
        topic_rating.incorrect_answers = topic_incorrect
        topic_rating.save()
    
    # ===============================================
    # BOSQICH 3: Fan reytingini yangilash (Subject)
    # ===============================================
    
    subject_rating, _ = SubjectRating.objects.get_or_create(
        user=user,
        subject=subject
    )
    
    # Fan bo'yicha barcha javoblar
    subject_answers = Answer.objects.filter(
        session__user=user,
        question__topic__subject=subject
    )
    
    subject_correct = sum(1 for a in subject_answers if a.is_correct)
    subject_incorrect = subject_answers.count() - subject_correct
    subject_tests = Answer.objects.filter(
        session__user=user,
        question__topic__subject=subject
    ).values_list('session_id', flat=True).distinct().count()
    
    subject_topics = Answer.objects.filter(
        session__user=user,
        question__topic__subject=subject
    ).values_list('question__topic_id', flat=True).distinct().count()
    
    if subject_answers.exists():
        subject_rating.stars = (subject_correct - subject_incorrect * 0.5) / subject_answers.count() * 5
        subject_rating.stars = max(0, min(5, subject_rating.stars))
        subject_rating.tests_completed = subject_tests
        subject_rating.topics_completed = subject_topics
        subject_rating.correct_answers = subject_correct
        subject_rating.incorrect_answers = subject_incorrect
        subject_rating.save()
    
    # ===============================================
    # BOSQICH 4: Davr reytinglarini yangilash
    # ===============================================
    
    today = timezone.now().date()
    
    # A) KUNLIK REYTING (Daily)
    daily_rating, daily_created = Rating.objects.get_or_create(
        user=user,
        period='daily',
        period_start_date=today,
        period_end_date=today
    )
    
    daily_answers = Answer.objects.filter(
        session__user=user,
        session__started_at__date=today
    )
    
    if daily_answers.exists():
        daily_correct = sum(1 for a in daily_answers if a.is_correct)
        daily_incorrect = daily_answers.count() - daily_correct
        daily_tests = daily_answers.values_list('session_id', flat=True).distinct().count()
        
        old_daily_stars = daily_rating.stars
        daily_rating.stars = (daily_correct - daily_incorrect * 0.5) / daily_answers.count() * 5
        daily_rating.stars = max(0, min(5, daily_rating.stars))
        daily_rating.tests_completed = daily_tests
        daily_rating.correct_answers = daily_correct
        daily_rating.incorrect_answers = daily_incorrect
        daily_rating.save()
        
        # RatingHistory yaratish (agar stars o'zgarsa)
        if not daily_created and old_daily_stars != daily_rating.stars:
            RatingHistory.objects.create(
                user=user,
                rating=daily_rating,
                previous_stars=old_daily_stars,
                new_stars=daily_rating.stars,
                stars_change=daily_rating.stars - old_daily_stars,
                reason="Kunlik test yakunlandi",
                test_session=test_session,
                period='daily'
            )
    
    # B) HAFTALIK REYTING (Weekly)
    week_start = today - timedelta(days=today.weekday())  # Dushanba
    week_end = week_start + timedelta(days=6)  # Yakshanba
    
    weekly_rating, weekly_created = Rating.objects.get_or_create(
        user=user,
        period='weekly',
        period_start_date=week_start,
        period_end_date=week_end
    )
    
    weekly_answers = Answer.objects.filter(
        session__user=user,
        session__started_at__date__gte=week_start,
        session__started_at__date__lte=week_end
    )
    
    if weekly_answers.exists():
        weekly_correct = sum(1 for a in weekly_answers if a.is_correct)
        weekly_incorrect = weekly_answers.count() - weekly_correct
        weekly_tests = weekly_answers.values_list('session_id', flat=True).distinct().count()
        
        old_weekly_stars = weekly_rating.stars
        weekly_rating.stars = (weekly_correct - weekly_incorrect * 0.5) / weekly_answers.count() * 5
        weekly_rating.stars = max(0, min(5, weekly_rating.stars))
        weekly_rating.tests_completed = weekly_tests
        weekly_rating.correct_answers = weekly_correct
        weekly_rating.incorrect_answers = weekly_incorrect
        weekly_rating.save()
        
        if not weekly_created and old_weekly_stars != weekly_rating.stars:
            RatingHistory.objects.create(
                user=user,
                rating=weekly_rating,
                previous_stars=old_weekly_stars,
                new_stars=weekly_rating.stars,
                stars_change=weekly_rating.stars - old_weekly_stars,
                reason="Haftalik test yakunlandi",
                test_session=test_session,
                period='weekly'
            )
    
    # C) UMUMIY REYTING (All-time)
    all_time_rating, all_time_created = Rating.objects.get_or_create(
        user=user,
        period='all_time',
        period_start_date=user.date_joined.date(),
        period_end_date=today
    )
    
    all_answers = Answer.objects.filter(session__user=user)
    
    if all_answers.exists():
        all_correct = sum(1 for a in all_answers if a.is_correct)
        all_incorrect = all_answers.count() - all_correct
        all_tests = all_answers.values_list('session_id', flat=True).distinct().count()
        
        old_all_stars = all_time_rating.stars
        all_time_rating.stars = (all_correct - all_incorrect * 0.5) / all_answers.count() * 5
        all_time_rating.stars = max(0, min(5, all_time_rating.stars))
        all_time_rating.tests_completed = all_tests
        all_time_rating.correct_answers = all_correct
        all_time_rating.incorrect_answers = all_incorrect
        all_time_rating.save()
        
        if not all_time_created and old_all_stars != all_time_rating.stars:
            RatingHistory.objects.create(
                user=user,
                rating=all_time_rating,
                previous_stars=old_all_stars,
                new_stars=all_time_rating.stars,
                stars_change=all_time_rating.stars - old_all_stars,
                reason="Umumiy reyting yangilandi",
                test_session=test_session,
                period='all_time'
            )
    
    # ===============================================
    # BOSQICH 5: Leaderboard'ni qayta hisoblash
    # ===============================================
    
    recalculate_leaderboard(user, today)


def recalculate_leaderboard(user=None, date=None):
    """
    Leaderboard'ni qayta hisoblash.
    
    Agar user berilsa, faqat shu user'ni yangilash.
    Agar date berilsa, shu sana uchun leaderboard yangilash.
    """
    
    if date is None:
        date = timezone.now().date()
    
    periods = ['daily', 'weekly', 'all_time']
    
    for period in periods:
        if period == 'daily':
            filter_date = date
            rating_filter = {
                'period': period,
                'period_start_date': filter_date,
                'period_end_date': filter_date
            }
        elif period == 'weekly':
            week_start = date - timedelta(days=date.weekday())
            rating_filter = {
                'period': period,
                'period_start_date': week_start,
                'period_end_date': week_start + timedelta(days=6)
            }
        else:  # all_time
            rating_filter = {'period': period}
        
        # Reyting bo'yicha barcha users'ni olish va ranking qilish
        if user:
            ratings = Rating.objects.filter(user=user, **rating_filter)
        else:
            ratings = Rating.objects.filter(**rating_filter)
        
        # Stars bo'yicha sort qilish
        ranked_users = []
        all_ratings = Rating.objects.filter(**rating_filter).order_by('-stars', '-tests_completed')
        
        for rank, rating in enumerate(all_ratings, 1):
            ranked_users.append((rank, rating))
        
        # Leaderboard'ni yangilash
        for rank, rating in ranked_users:
            leaderboard_entry, _ = Leaderboard.objects.update_or_create(
                user=rating.user,
                period=period,
                date=date,
                defaults={
                    'rank': rank,
                    'stars': rating.stars,
                    'tests_completed': rating.tests_completed
                }
            )


# Signals'ni ro'yxatga qo'shish
from django.apps import AppConfig

class ProgressConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'progress'
    
    def ready(self):
        import progress.signals  # Signal'larni yuklash
```

---

## ⚙️ Qadam 2: Signal Ro'yxatga Qo'shish

```python
# progress/apps.py

from django.apps import AppConfig

class ProgressConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'progress'
    
    def ready(self):
        import progress.signals  # Bu qatorda signals yuklanaadi
```

---

## 🔄 Qadam 3: Rating Calculation Service (Optional)

```python
# rating/services.py

from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from testengine.models import Answer
from rating.models import Rating, Leaderboard
from catalog.models import Topic, Subject


class RatingService:
    """Rating hisoblash uchun service"""
    
    @staticmethod
    def calculate_stars_from_answers(answers_queryset):
        """
        Javoblar to'plamidan stars hisoblash.
        
        Formula: (To'g'ri - Noto'g'ri * 0.5) / Jami * 5
        """
        if not answers_queryset.exists():
            return 0.0
        
        correct = sum(1 for a in answers_queryset if a.is_correct)
        incorrect = answers_queryset.count() - correct
        
        stars = (correct - incorrect * 0.5) / answers_queryset.count() * 5
        return max(0, min(5, stars))
    
    @staticmethod
    def get_user_rank(user, period, date=None):
        """
        User'ning reytingdagi o'rni.
        """
        if date is None:
            date = timezone.now().date()
        
        if period == 'daily':
            rating = Rating.objects.filter(
                user=user,
                period='daily',
                period_start_date=date,
                period_end_date=date
            ).first()
        elif period == 'weekly':
            week_start = date - timedelta(days=date.weekday())
            rating = Rating.objects.filter(
                user=user,
                period='weekly',
                period_start_date=week_start
            ).first()
        else:  # all_time
            rating = Rating.objects.filter(user=user, period='all_time').first()
        
        if not rating:
            return None
        
        # Bu user'dan yuqori stars'ga ega bo'lganlarni hisoblash
        higher_stars = Rating.objects.filter(
            period=rating.period,
            period_start_date=rating.period_start_date,
            stars__gt=rating.stars
        ).count()
        
        return higher_stars + 1  # 1-indexed rank
    
    @staticmethod
    def get_top_users(period, limit=100, date=None):
        """
        Period bo'yicha top users'ni olish.
        """
        if date is None:
            date = timezone.now().date()
        
        if period == 'daily':
            ratings = Rating.objects.filter(
                period='daily',
                period_start_date=date,
                period_end_date=date
            ).order_by('-stars', '-tests_completed')[:limit]
        elif period == 'weekly':
            week_start = date - timedelta(days=date.weekday())
            ratings = Rating.objects.filter(
                period='weekly',
                period_start_date=week_start
            ).order_by('-stars', '-tests_completed')[:limit]
        else:  # all_time
            ratings = Rating.objects.filter(
                period='all_time'
            ).order_by('-stars', '-tests_completed')[:limit]
        
        return ratings
```

---

## 📝 IMPLEMENTATION CHECKLIST

- [ ] `progress/signals.py` faylini yaratish va signal yozish
- [ ] `progress/apps.py`'ga signal import qilish
- [ ] `rating/services.py` yaratish (optional lekin recommended)
- [ ] Signals'ni test qilish (test case'lar yozish)
- [ ] Celery task yaratish (vaqtga qarab Leaderboard yangilash)
- [ ] Management command yaratish (`python manage.py recalculate_ratings`)

---

## 🧪 TESTING

```python
# rating/tests.py

from django.test import TestCase, TransactionTestCase
from testengine.models import TestSession, Answer
from catalog.models import Subject, Topic, Question
from account.models import User
from rating.models import Rating, RatingHistory, TopicRating


class RatingCalculationTest(TransactionTestCase):
    """Rating hisoblash logikasini test qilish"""
    
    def setUp(self):
        # User yaratish
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Subject, Topic, Question yaratish
        self.subject = Subject.objects.create(name='Matematika')
        self.topic = Topic.objects.create(subject=self.subject, name='Kvadrat tenglamalar')
        self.question = Question.objects.create(
            topic=self.topic,
            text='2x^2 + 3x + 1 = 0?',
            options={'A': '1', 'B': '-1', 'C': '0.5', 'D': '-0.5'},
            correct_option='B',
            difficulty=2
        )
    
    def test_rating_created_after_test(self):
        """Test yakunidan keyin rating yaratilishi kerak"""
        
        # TestSession yaratish
        session = TestSession.objects.create(
            user=self.user,
            subject=self.subject
        )
        
        # Answer yaratish (1 ta to'g'ri)
        Answer.objects.create(
            session=session,
            question=self.question,
            selected_option='B',
            is_correct=True,
            time_spent_seconds=30
        )
        
        # TestResult yaratish (signal triggerlash)
        from testengine.models import TestResult
        result = TestResult.objects.create(
            session=session,
            total_score=100,
            correct_count=1,
            incorrect_count=0,
            duration_seconds=30
        )
        
        # Rating'lar yaratilganini tekshirish
        daily_rating = Rating.objects.filter(
            user=self.user,
            period='daily'
        ).first()
        
        self.assertIsNotNone(daily_rating)
        self.assertEqual(daily_rating.tests_completed, 1)
        self.assertEqual(daily_rating.correct_answers, 1)
```

---

## 🚀 DEPLOYMENT CHECKLIST

- [ ] Signals test qilindi
- [ ] Migrations test qilindi
- [ ] Production database'ga migrations qo'llanildi
- [ ] Monitoring setup qilindi (signal errors uchun)
- [ ] Celery tasks qo'shildi (agar kerak)
- [ ] Backup olingan

---

**✍️ Implementation vaqti:** ~8-10 soat (signals + tests + deployment)

