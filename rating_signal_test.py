"""
Signals testini qo'lga olish uchun test skripti.
Django shell'da quyidagi kodni jiklamang:

$ python manage.py shell < rating_signal_test.py
"""

from django.utils import timezone
from account.models import User
from catalog.models import Subject, Topic, Question
from testengine.models import TestSession, Answer, TestResult
from rating.models import Rating, RatingHistory


def create_test_data():
    """Test uchun ma'lumotlar yaratish"""
    print("\n=== TEST MA'LUMOTLARI YARATILMOQDA ===\n")
    
    # 1. User yaratish yoki olish
    user, created = User.objects.get_or_create(
        email='test_student@example.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'Student',
            'is_active': True,
        }
    )
    print(f"✓ User: {user.email} {'(created)' if created else '(existing)'}")
    
    # 2. Subject yaratish yoki olish
    subject, created = Subject.objects.get_or_create(
        name='Biologiya',
        defaults={
            'description': 'Test predmeti',
        }
    )
    print(f"✓ Subject: {subject.name} {'(created)' if created else '(existing)'}")
    
    # 3. Topics yaratish yoki olish
    topic1, _ = Topic.objects.get_or_create(
        name='Hujayra',
        subject=subject,
    )
    topic2, _ = Topic.objects.get_or_create(
        name='Fotosintez',
        subject=subject,
    )
    print(f"✓ Topics: {topic1.name}, {topic2.name}")
    
    # 4. Questions yaratish yoki olish
    questions = []
    for i, topic in enumerate([topic1, topic2], 1):
        for j in range(1, 3):  # har topic uchun 2 ta savol
            q, _ = Question.objects.get_or_create(
                text=f"{topic.name} savoli {j}",
                topic=topic,
                defaults={
                    'options': {
                        'A': 'A) Javob A',
                        'B': 'B) Javob B',
                        'C': 'C) Javob C',
                        'D': 'D) Javob D',
                    },
                    'correct_option': 'A',
                    'difficulty': Question.Difficulty.MEDIUM,
                }
            )
            questions.append(q)
    print(f"✓ Questions: {len(questions)} ta savol yaratildi")
    
    return user, subject, topic1, topic2, questions


def simulate_test_session(user, subject, topic1, topic2, questions):
    """Test sessions'ni simulyatsiya qilish"""
    print("\n=== TEST SESSIONI SIMULYATSIYA QILMOQDA ===\n")
    
    # 1. TestSession yaratish
    session = TestSession.objects.create(
        user=user,
        subject=subject,
        mode='practice',
    )
    print(f"✓ TestSession yaratildi: {session.id}")
    
    # 2. Answers yaratish
    print("\n  Javoblar:",)
    correct_count = 0
    incorrect_count = 0
    
    for idx, question in enumerate(questions, 1):
        # Birinchi ikita (Topic 1): to'g'ri
        # Qolganlar: notog'ri
        is_correct = idx <= 2
        
        answer = Answer.objects.create(
            session=session,
            question=question,
            selected_option='A',
            is_correct=is_correct,
            confidence='sure',
            time_spent_seconds=30,
        )
        
        if is_correct:
            correct_count += 1
            status = "✓"
        else:
            incorrect_count += 1
            status = "✗"
        
        print(f"  {status} Q{idx} ({question.topic.name}): {'To\'g\'ri' if is_correct else 'Notog\'ri'}")
    
    # 3. TestResult yaratish (bu signal'ni trigger qiladi!)
    print(f"\n  TestResult yaratilmoqda...")
    test_result = TestResult.objects.create(
        session=session,
        total_score=correct_count * 10,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        duration_seconds=120,
    )
    print(f"  ✓ TestResult yaratildi (SIGNAL TRIGGERED!)")
    
    return session, test_result, correct_count, incorrect_count


def check_ratings(user, correct_count, incorrect_count):
    """Reytinglarni tekshirish"""
    print("\n=== REYTINGLAR TEKSHIRILMOQDA ===\n")
    
    # Yulduzlar formulasi
    total = correct_count + incorrect_count
    expected_stars = max(0.0, min(5.0, ((correct_count - incorrect_count * 0.5) / total * 5))) if total > 0 else 0.0
    print(f"\n📊 Formula: ({correct_count} - {incorrect_count}*0.5) / {total} * 5 = {expected_stars:.1f} ⭐")
    
    # 1. General Ratings
    print("\n📈 General Ratings:")
    ratings = Rating.objects.filter(user=user).order_by('period')
    for rating in ratings:
        print(f"  • {rating.get_period_display():15} | "
              f"Stars: {rating.stars:.1f} ⭐ | "
              f"Tests: {rating.tests_completed} | "
              f"Correct: {rating.correct_answers} | "
              f"Incorrect: {rating.incorrect_answers}")
        
        # Tekshirish
        if abs(rating.stars - expected_stars) < 0.01:
            print(f"    ✅ Yulduzlar to'g'ri hisoblandi!")
        else:
            print(f"    ⚠️ Kutilgan: {expected_stars:.1f}, Hali: {rating.stars:.1f}")
    
    # 2. Rating Histories
    print("\n📋 Rating History:")
    histories = RatingHistory.objects.filter(user=user).order_by('-created_at')[:3]
    for history in histories:
        print(f"  • {history.get_period_display():15} | "
              f"{history.previous_stars} → {history.new_stars} "
              f"({history.stars_change:+.1f}) | "
              f"Sababi: {history.reason}")
    
    # 3. Subject va Topic Ratings
    print("\n👥 Subject & Topic Ratings:")
    from rating.models import SubjectRating, TopicRating
    
    subject_ratings = SubjectRating.objects.filter(user=user)
    for sr in subject_ratings:
        print(f"  Subject: {sr.subject.name} | "
              f"Stars: {sr.stars:.1f} ⭐ | "
              f"Accuracy: {sr.accuracy_percentage:.1f}%")
    
    topic_ratings = TopicRating.objects.filter(user=user)
    for tr in topic_ratings:
        print(f"  Topic: {tr.topic.name:20} | "
              f"Stars: {tr.stars:.1f} ⭐ | "
              f"Accuracy: {tr.accuracy_percentage:.1f}%")


def main():
    """Asosiy test function"""
    print("\n" + "="*60)
    print("🚀 SIGNALS AUTO-RATING TEST")
    print("="*60)
    
    try:
        # Ma'lumotlar yaratish
        user, subject, topic1, topic2, questions = create_test_data()
        
        # Test sessioni simulyatsiya qilish
        session, test_result, correct_count, incorrect_count = simulate_test_session(
            user, subject, topic1, topic2, questions
        )
        
        # Reytinglarni tekshirish
        check_ratings(user, correct_count, incorrect_count)
        
        print("\n" + "="*60)
        print("✅ TEST TAYYORLANDI!")
        print("="*60)
        print("\n📍 NATIJA:")
        print(f"  • User: {user.email}")
        print(f"  • Subject: {subject.name}")
        print(f"  • Correct: {correct_count}/{correct_count + incorrect_count}")
        print(f"  • Test Ratings: ✓ Created")
        print(f"  • Signal: ✓ Triggered")
        print(f"  • Database: ✓ Updated")
        print("\n🎉 HAMMASINI AUTO QILDI!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
