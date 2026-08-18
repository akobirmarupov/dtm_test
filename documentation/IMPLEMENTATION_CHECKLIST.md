# 📋 IMPLEMENTATION CHECKLIST - DTM TEST PLATFORM

## ⚠️ JORIY HOLAT (CURRENT STATE)

### ✅ TAYYOR (DONE):
- [x] Database models va structure
- [x] Google OAuth authentication
- [x] Test engine API (sessions, answers, results)
- [x] Progress tracking (streak, XP, review cards)
- [x] Billing models (plans, subscriptions, payments)
- [x] Catalog models (subjects, topics, questions)
- [x] Django admin panel (Unfold)

### ⏳ QILISH KERAK (TO DO):
- [ ] Frontend (React/Vue)
- [ ] Notification system
- [ ] Admin dashboard
- [ ] Mentor dashboard
- [ ] Analytics
- [ ] Payment provider integration

---

## 🎯 PHASE 1: API COMPLETION (3-5 HAFTA)

### Week 1-2: API Views va Endpoints Yaratish

#### Catalog App Views (20-25 soat):
```python
# catalog/routes/views.py ga qo'shimcha:

class SubjectListCreateAPIView(ListCreateAPIView):
    """Fan ro'yxati va yaratish (Admin)"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Admin permissions check
        if not self.request.user.is_staff:
            raise PermissionDenied("Faqat admin qilishi mumkin")
        serializer.save()

class TopicListCreateAPIView(ListCreateAPIView):
    """Mavzular"""
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = TopicFilter

class QuestionListCreateAPIView(ListCreateAPIView):
    """Savollar"""
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = QuestionFilter
```

**Checklist:**
- [ ] SubjectListCreateAPIView ✓ (List, Create)
- [ ] SubjectDetailAPIView ✓ (Retrieve, Update, Delete)
- [ ] TopicListCreateAPIView ✓ (List, Create)
- [ ] TopicDetailAPIView ✓ (Retrieve, Update, Delete)
- [ ] QuestionListCreateAPIView ✓ (List, Create)
- [ ] QuestionDetailAPIView ✓ (Retrieve, Update, Delete)
- [ ] Test all endpoints in Postman
- [ ] Add pagination
- [ ] Add filtering (by subject_id, difficulty, etc.)

---

#### Progress App Views (15-20 soat):

```python
# progress/routes/reviewcard_view.py:

class ReviewCardListAPIView(ListAPIView):
    """Barcha review kartalari"""
    queryset = ReviewCard.objects.all()
    serializer_class = ReviewCardSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

class ReviewCardTodayAPIView(ListAPIView):
    """Bugun takrorlash kerak bo'lgan"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        today = timezone.now().date()
        return ReviewCard.objects.filter(
            user=self.request.user,
            next_review_date=today
        )

class ReviewCardSubmitAPIview(APIView):
    """Takrorlash yechildi"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        review_card = ReviewCard.objects.get(id=pk)
        is_correct = request.data.get('is_correct')
        
        # FSRS algoritmi bilan update
        if is_correct:
            review_card.stability_days *= 2
        else:
            review_card.stability_days = max(1, review_card.stability_days / 2)
        
        review_card.next_review_date = (
            timezone.now().date() + 
            timedelta(days=review_card.stability_days)
        )
        review_card.save()
        
        return Response(ReviewCardSerializer(review_card).data)
```

**Checklist:**
- [ ] ReviewCardListAPIView ✓
- [ ] ReviewCardTodayAPIView ✓
- [ ] ReviewCardSubmitAPIview ✓ (FSRS algorithm implement)
- [ ] StreakDetailAPIView ✓
- [ ] StreakFreezeAPIView ✓ (Check freezes_available)
- [ ] XPTransactionListAPIView ✓
- [ ] XPSummaryAPIView ✓
- [ ] WeeklyLeaderboardAPIView ✓

---

#### Billing App Views (12-15 soat):

```python
# billing/routes/plan/views.py:

class PlanCreateListAPIView(ListCreateAPIView):
    """Obuna rejalaari"""
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]

# billing/routes/subscription/views.py:

class SubscriptionListAPIView(ListAPIView):
    """Barcha obunaalar"""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

class SubscriptionCurrentAPIView(RetrieveAPIView):
    """Joriy obuna"""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return Subscription.objects.filter(
            user=self.request.user,
            status=Subscription.Status.ACTIVE
        ).first()

class SubscriptionCancelAPIView(APIView):
    """Obunani bekor qilish"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        subscription = Subscription.objects.get(id=pk, user=request.user)
        subscription.status = Subscription.Status.CANCELLED
        subscription.save()
        
        return Response(SubscriptionSerializer(subscription).data)

# billing/routes/payment/views.py:

class PaymentCreateListAPIView(ListCreateAPIView):
    """To'lov qilish"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        payment = serializer.save(user=self.request.user)
        # Payme/Click API-ga yo'naltirish
        redirect_url = initiate_payment(payment)
        return Response({
            'payment_id': payment.id,
            'redirect_url': redirect_url
        })

class PaymentApproveAPIView(APIView):
    """To'lovni tasdiqlash (Admin)"""
    permission_classes = [IsAdminUser]
    
    def post(self, request, pk):
        payment = Payment.objects.get(id=pk)
        payment.status = Payment.Status.SUCCESS
        payment.save()
        
        # Obunani activate qilish
        subscription = payment.subscription
        subscription.status = Subscription.Status.ACTIVE
        subscription.save()
        
        return Response(PaymentSerializer(payment).data)
```

**Checklist:**
- [ ] PlanCreateListAPIView ✓ (List, Create - Admin only)
- [ ] PlanDetailAPIView ✓
- [ ] SubscriptionListAPIView ✓
- [ ] SubscriptionCurrentAPIView ✓
- [ ] SubscriptionCancelAPIView ✓
- [ ] PaymentCreateListAPIView ✓
- [ ] PaymentApproveAPIView ✓ (Admin)
- [ ] PaymentRejectAPIView ✓ (Admin)
- [ ] Integrate Payme API
- [ ] Integrate Click API

---

### Week 2-3: Serializers va Validation (10-15 soat)

**catalog/routes/serializers.py:**
```python
class SubjectSerializer(serializers.ModelSerializer):
    topics_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Subject
        fields = ['id', 'name', 'topics_count', 'created_at']
    
    def get_topics_count(self, obj):
        return obj.topics.count()

class TopicSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    class Meta:
        model = Topic
        fields = ['id', 'name', 'subject_id', 'subject_name', 'questions_count']

class QuestionSerializer(serializers.ModelSerializer):
    """Test enginedan faqat correct_option yo'q"""
    class Meta:
        model = Question
        fields = ['id', 'text', 'options', 'difficulty', 'topic_id']

class QuestionDetailSerializer(serializers.ModelSerializer):
    """Admin uchun correct_option bilan"""
    class Meta:
        model = Question
        fields = '__all__'
```

**Checklist:**
- [ ] SubjectSerializer
- [ ] TopicSerializer
- [ ] QuestionSerializer (2 versiyasi)
- [ ] ReviewCardSerializer
- [ ] StreakSerializer
- [ ] XPTransactionSerializer
- [ ] LeaderboardSerializer
- [ ] PlanSerializer
- [ ] SubscriptionSerializer
- [ ] PaymentSerializer
- [ ] Validation qo'shish (blank/null checks)

---

### Week 3: Permissions va Throttling (8-10 soat)

**common/permissions.py:**
```python
from rest_framework.permissions import BasePermission

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == Role.STUDENT

class IsMentor(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in [Role.MENTOR, Role.ADMIN]

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == Role.ADMIN
```

**Checklist:**
- [ ] IsStudent permission
- [ ] IsMentor permission  
- [ ] IsAdmin permission
- [ ] AnonBurstRateThrottle (20 req/min)
- [ ] BurstUserRateThrottle (100 req/min)
- [ ] SustainedUserRateThrottle (1000 req/hour)
- [ ] Apply to all views

---

### Week 3-4: Testing (10-15 soat)

**Postman + Pytest:**
- [ ] Login endpoint test
- [ ] Test session create/list/finish
- [ ] Answer create/list
- [ ] Review card submit
- [ ] Streak freeze
- [ ] XP calculation
- [ ] Payment flow
- [ ] Permission checks
- [ ] Error handling

---

## 🎨 PHASE 2: FRONTEND DEVELOPMENT (4-6 HAFTA)

### Technology Stack:
```
Frontend: React 18 + TypeScript
State Management: Redux Toolkit / Zustand
HTTP Client: Axios / Fetch API
UI Library: Material-UI / Tailwind CSS
Routing: React Router v6
```

### Week 1-2: Project Setup va Core Screens (15-20 soat)

```
src/
├── components/
│   ├── Auth/
│   │   ├── GoogleLogin.tsx
│   │   ├── ProtectedRoute.tsx
│   └── Layout/
│       ├── Header.tsx
│       ├── BottomNav.tsx
│       └── Layout.tsx
├── pages/
│   ├── LoginPage.tsx
│   ├── HomePage.tsx
│   ├── TestPage.tsx
│   ├── ResultPage.tsx
│   ├── ReviewPage.tsx
│   ├── ProfilePage.tsx
│   └── PremiumPage.tsx
├── services/
│   ├── api.ts (Axios instance)
│   ├── authService.ts
│   ├── testService.ts
│   ├── progressService.ts
│   └── billingService.ts
├── store/
│   ├── authSlice.ts
│   ├── testSlice.ts
│   └── progressSlice.ts
└── utils/
    ├── constants.ts
    └── helpers.ts
```

**Checklist:**
- [ ] Create React app + TypeScript
- [ ] Setup routing (React Router)
- [ ] Setup Redux/Zustand
- [ ] Create API service layer
- [ ] Implement LoginPage (Google OAuth)
- [ ] Implement HomePage (dashboard)
- [ ] Implement TestPage (question flow)
- [ ] Implement ResultPage
- [ ] Implement ReviewPage
- [ ] Implement ProfilePage
- [ ] Implement PremiumPage
- [ ] Add responsive design

---

### Week 2-3: Integration (12-15 soat)

- [ ] Connect all API endpoints
- [ ] Add JWT token management
- [ ] Add error handling (try/catch + UI feedback)
- [ ] Add loading states
- [ ] Add success/error notifications
- [ ] Add offline support (localStorage)

---

### Week 3-4: Polish (10-12 soat)

- [ ] Add animations
- [ ] Add optimistic updates
- [ ] Add analytics tracking
- [ ] Add error logging
- [ ] Performance optimization
- [ ] SEO (if needed)

---

## 🔔 PHASE 3: NOTIFICATIONS (1-2 HAFTA)

### SMS Notifications:
```python
# notifications/services/sms.py

def send_sms(phone_number, message):
    """Uzinfon/Perfectum orqali SMS yuborish"""
    # API integration
    response = requests.post(
        'https://api.uzinfon.uz/api/send-sms',
        json={
            'phone': phone_number,
            'message': message,
            'from': 'TestYourself'
        }
    )
    return response.status_code == 200

# Progress signal listeners:
from django.db.models.signals import post_save

@receiver(post_save, sender=Streak)
def notify_streak_milestone(sender, instance, **kwargs):
    """Streak milestone-da SMS yuborish"""
    if instance.current_streak == 7:
        send_sms(instance.user.phone, "Afarin! 7 kunlik streak!")
    elif instance.current_streak == 30:
        send_sms(instance.user.phone, "Tabriklaymiz! 30 kunlik streak!")
```

**Checklist:**
- [ ] Setup Celery (background tasks)
- [ ] Integrate SMS provider (Uzinfon/Perfectum)
- [ ] Implement review reminders
- [ ] Implement streak reminders
- [ ] Implement payment confirmation
- [ ] Setup email notifications
- [ ] Setup push notifications (FCM)

---

## 👨‍💼 PHASE 4: ADMIN DASHBOARD (1-2 HAFTA)

### Django Admin Customization (unfold):
```python
# account/admin.py

@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('email', 'full_name', 'role', 'xp_total', 'is_active')
    list_filter = ('role', 'created_at')
    search_fields = ('email', 'full_name')
    fieldsets = (
        ('Asosiy Ma\'lumot', {
            'fields': ('email', 'full_name', 'avatar_url')
        }),
        ('Profil', {
            'fields': ('role', 'region', 'target_major', 'xp_total')
        }),
        ('Huquqlar', {
            'fields': ('is_active', 'is_staff', 'groups')
        }),
    )
```

**Checklist:**
- [ ] Customize Django admin (Unfold)
- [ ] Add user management
- [ ] Add content management (subjects, topics, questions)
- [ ] Add analytics dashboard
- [ ] Add payment management
- [ ] Add subscriber filtering

---

## 👨‍🏫 PHASE 5: MENTOR DASHBOARD (2-3 HAFTA)

### Frontend Routes:
```
/mentor/
├── /mentor/students        # Barcha talabalar
├── /mentor/students/:id    # Talaba progress
├── /mentor/analytics       # Umumiy statistika
└── /mentor/reports         # Report yaratish
```

### API Endpoints (New):
```
GET /mentor/students/              # Foydalanuvchining talabalaari
GET /mentor/students/{id}/progress # Talabaning progress
GET /mentor/students/{id}/results  # Talabaning natijalaari
GET /mentor/analytics/             # Analytics
```

**Checklist:**
- [ ] Create MentorLayout component
- [ ] Create StudentListPage
- [ ] Create StudentProgressPage
- [ ] Create AnalyticsPage
- [ ] Add filtering/sorting
- [ ] Add export to PDF/Excel

---

## 📊 PHASE 6: ANALYTICS (1-2 HAFTA)

### Tracking Points:
- Test completion rate
- Average score by subject
- Most difficult questions
- Learner retention
- Streak statistics
- XP distribution

```python
# analytics/views.py

class AnalyticsView(APIView):
    def get(self, request):
        # Total users
        total_users = User.objects.count()
        
        # Active users (last 7 days)
        active_users = User.objects.filter(
            test_sessions__started_at__gte=timezone.now() - timedelta(days=7)
        ).distinct().count()
        
        # Average score
        avg_score = TestResult.objects.aggregate(
            avg_score=Avg('total_score')
        )['avg_score']
        
        # Top subjects
        top_subjects = Subject.objects.annotate(
            avg_score=Avg('test_sessions__result__total_score')
        ).order_by('-avg_score')[:5]
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'avg_score': avg_score,
            'top_subjects': TopSubjectSerializer(top_subjects, many=True).data
        })
```

**Checklist:**
- [ ] Create analytics models
- [ ] Create analytics views
- [ ] Implement caching (Redis)
- [ ] Create analytics frontend
- [ ] Add charts/graphs (Chart.js)

---

## 🧪 PHASE 7: TESTING (1-2 HAFTA)

### Backend Testing:
```python
# testengine/tests/test_views.py

class TestSessionViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@test.com')
        self.subject = Subject.objects.create(name='Matematika')
    
    def test_create_session(self):
        response = self.client.post(
            '/testengine/sessions/',
            {'subject_id': self.subject.id, 'mode': 'practice'},
            headers={'Authorization': f'Bearer {self.token}'}
        )
        self.assertEqual(response.status_code, 201)
    
    def test_answer_question(self):
        session = TestSession.objects.create(user=self.user, subject=self.subject)
        response = self.client.post(
            f'/testengine/sessions/{session.id}/answers/',
            {'question_id': 1, 'selected_option': 'A'},
            headers={'Authorization': f'Bearer {self.token}'}
        )
        self.assertEqual(response.status_code, 201)
```

**Checklist:**
- [ ] Unit tests (Backend)
- [ ] Integration tests
- [ ] E2E tests (Cypress/Playwright)
- [ ] Load testing
- [ ] Security testing
- [ ] API documentation (Swagger)

---

## 🚀 DEPLOYMENT (FINAL PHASE)

### Production Checklist:
- [ ] Environment variables (.env)
- [ ] Database migrations
- [ ] Static files collection
- [ ] SSL certificate
- [ ] CDN setup
- [ ] Database backups
- [ ] Logging setup
- [ ] Monitoring (Sentry/DataDog)
- [ ] CI/CD pipeline (GitHub Actions)

---

## 📅 TIMELINE

```
Week 1-2:    API completion
Week 3-4:    Frontend MVP
Week 5-6:    Integration + Testing
Week 7:      Notifications
Week 8:      Admin Dashboard
Week 9:      Mentor Dashboard + Analytics
Week 10:     Final testing + Deployment
```

**Total: ~10 hafta (2.5 oy)**

---

## 💾 VERSION CONTROL

```bash
# Main branch: production
# Development branches:
git checkout -b feature/catalog-api
git checkout -b feature/frontend-setup
git checkout -b feature/notifications
git checkout -b feature/admin-dashboard

# Commit message format:
git commit -m "feat(catalog): add question list endpoint"
git commit -m "fix(auth): fix Google token verification"
git commit -m "docs(api): update API documentation"
```

---

## 🎯 SUCCESS CRITERIA

- [x] All API endpoints working
- [ ] 80%+ test coverage
- [ ] Frontend fully functional
- [ ] Mobile responsive
- [ ] Performance < 3 seconds
- [ ] Uptime 99.9%
- [ ] No critical security issues
- [ ] Users can login → test → see results
- [ ] Premium subscription working
- [ ] Notifications sending

---

## 📞 CONTACT & SUPPORT

- **Backend Issues**: Check Django logs
- **Frontend Issues**: Check browser console
- **Database Issues**: Check PostgreSQL logs
- **Payment Issues**: Check Payme/Click API logs

---

**GOOD LUCK! 🚀**

Agar savol bo'lsa, AI asistentdan foydalaning yoki Mentor-ni chaqiring!
