
TESTYOURSELF
Backend (Python) — Стажёр дастурчи учун ментор қўлланмаси
ҚАДАМБА-ҚАДАМ ЙЎЛ ХАРИТАСИ
UNIVORA (Realsoft Academy LLC)  ·  2026
Бу қўлланма ҳақида
• Ушбу ҳужжат «TestYourself» техник топшириғи (ТЗ MVP) асосида, backend қисмини Python'да ёзадиган амалиётчи-стажёр учун тайёрланган.
• Услуб — senior дастурчи-ментор ўз стажёрини қўлдан етаклаб, модулма-модул ўргатиши шаклида қурилган.
• Ҳар бир қадамда: нима учун шундай қиламиз, қандай қиламиз (код намунаси), ва кўп учрайдиган хатолар кўрсатилган.
• Технология танлови: Python + Django + Django REST Framework (DRF) — стажёр учун энг тушунарли, «batteries-included» ва ишончли стек.


Ментордан кириш сўзи
Салом! Мен — сенинг ментор сифатидаги йўлдошинг бу йўлда. Ушбу қўлланма сени «TestYourself» лойиҳасининг backend қисмини ноldan бошлаб, боскичма-босқич қуришга йўналтиради. Мақсадимиз — сени фақат «кодни кўчириб ёзадиган» эмас, балки ҳар бир қарорнинг НЕГА шундай қабул қилинганини тушунадиган дастурчи қилиб етиштириш.
Муҳим тамойил: биз ҳар доим энг содда ишлайдиган ечимдан бошлаймиз (MVP тамойили), кейин уни такомиллаштирамиз. Мукаммал кодни биринчи уринишда ёзишга ҳаракат қилма — аввал ИШЛАЙДИГАН кодни ёз, кейин уни яхшила (тестла, рефактор қил).
Ушбу қўлланмадан қандай фойдаланиш керак
•Қадамларни кетма-кет бажар: ҳар бир қадам олдингисига асосланади, шошилмасдан ўтишингни тавсия қиламан
•Ҳар бир кодни ўзинг қўлингиз билан қайта ёз: copy-paste қилиш эмас, тера-тера ёзиш хотирада яхши сақланади
•«🎓 Ментордан маслаҳат» ва «⚠ Хато» блокларини диққат билан ўқи: булар йиллар давомида тўпланган тажриба хулосалари
•AI-ёрдамчидан фойдалан, лекин тушунмасдан қабул қилма: ТЗ'нинг 11-бўлимида айтилганидек, AI сенинг жуниор ёрдамчинг, устозинг эмас — ҳар бир таклифни тушуниб, текшириб ол
Бошлашдан олдин: муҳитни тайёрлаш
Керакли билим даражаси
Бу қўлланма учун сендан қуйидагиларни билишинг кутилади: Python асослари (функциялар, класслар, list/dict), HTTP нима эканини тушуниш (GET/POST/PUT/DELETE), Git билан асосий ишлаш (commit, push, branch). Django'ни билиш шарт эмас — биз ноldan ўрганамиз.
Керакли dasturiy ta'minot
Восита	Мақсад
Python 3.11+	Асосий дастурлаш тили
PostgreSQL 15+	Асосий маълумотлар базаси
Redis	Кэш ва навбат (queue) учун
Git	Версия бошқаруви
VS Code ёки PyCharm	Код муҳити (IDE)
Postman ёки Thunder Client	API'ни қўлда синаш учун
Муҳитни созлаш
Terminal
# 1. Virtual environment yaratish (loyihani izolyatsiya qilish uchun)
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
 
# 2. Asosiy kutubxonalarni o'rnatish
pip install django djangorestframework psycopg2-binary
pip install django-cors-headers python-decouple redis celery
pip install djangorestframework-simplejwt
🎓 Ментордан маслаҳат
Virtual environment (venv) — бу сенинг лойиҳангнинг «ўз хонаси». Уни ҳар доим ишлатишни одат қил, чунки бошқа лойиҳаларнинг кутубхона версиялари билан тўқнашмайди. Ҳеч қачон venv'сиз глобал equrilmaga pip install қилма!
0-қадам. Лойиҳа скелетини яратиш
Django'да лойиҳа икки даражали тузилишга эга: ташқи «project» (созламалар) ва ичкарида бир нечта «app» (ҳар бир app — алоҳида модул, масалан: фойдаланувчилар, тестлар).
Terminal
django-admin startproject config .
python manage.py startapp accounts     # foydalanuvchilar va autentifikatsiya
python manage.py startapp testengine    # fanlar, savollar, test sessiyalari
python manage.py startapp progress       # natija tahlili, streak, FSRS
python manage.py startapp billing        # obuna va to'lov
Натижада лойиҳа тузилиши қуйидагича бўлади:
Loyiha tuzilishi
testyourself/
├── config/            # loyiha sozlamalari (settings.py, urls.py)
├── accounts/          # User modeli, OTP, JWT autentifikatsiya
├── testengine/        # Subject, Question, TestSession, Answer
├── progress/          # ReviewCard (FSRS), Streak, tahlil logikasi
├── billing/           # Subscription, Payment
├── manage.py
└── requirements.txt
•Нима учун бир нечта app: ТЗ'нинг 5-бўлимида айтилганидек, тизимни модулларга ажратиш келажакда микросервисларга ўтишни осонлаштиради. Ҳар бир app ўз ичида мустақил, ўз моделлари ва API'сига эга.
⚠ Стажёрлар кўп йўл қўядиган хато
Кўп стажёрлар бутун лойиҳани биттa катта app'га (масалан, «main») жойлаштиради. Бу дастлаб қулай туюлади, лекин лойиҳа ўсганда кодни топиш ва тест қилиш қийинлашади. Ҳар доим модулларга ажратиб бошла — кейин уларни бирлаштириш осон, лекин ажратилмаган каттa кодни бўлиш жуда қийин.
1-қадам. Маълумотлар модели (models.py)
Бу — лойиҳанинг «пойдевори». ТЗ'нинг 9-бўлимидаги Entity жадвалини энди Python кодига айлантирамиз. Аввал энг муҳим иккита моделдан бошлаймиз: фойдаланувчи ва тест таркиби.
1.1. Фойдаланувчи модели (accounts/models.py)
accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
 
class User(AbstractUser):
    phone_number = models.CharField(max_length=20, unique=True)
    region = models.CharField(max_length=100, blank=True)
    target_major = models.CharField(max_length=150, blank=True)
    xp_total = models.PositiveIntegerField(default=0)
    consent_share_with_universities = models.BooleanField(default=False)
    consent_updated_at = models.DateTimeField(null=True, blank=True)
 
    def __str__(self):
        return self.phone_number
🎓 Ментордан маслаҳат
Диққат: биз Django'нинг тайёр AbstractUser классидан мерос (inherit) оляпмиз, ноldan ёзмаяпмиз. Бу — «g'ildirakni qayta ixtiro qilma» тамойили: parol хэшлаш, autentifikatsiya каби мураккаб ва хавфсизлик-критик нарсалар Django'да аллақачон синалган ва хавфсиз ёзилган.
1.2. Тест таркиби модели (testengine/models.py)
testengine/models.py
from django.db import models
from accounts.models import User
 
class Subject(models.Model):
    name = models.CharField(max_length=100)          # masalan: Matematika
 
class Topic(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=150)          # masalan: Kvadrat tenglamalar
 
class Question(models.Model):
    DIFFICULTY_CHOICES = [(i, str(i)) for i in range(1, 6)]
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    options = models.JSONField()          # masalan: {"A": "...", "B": "..."}
    correct_option = models.CharField(max_length=1)
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=3)
 
class TestSession(models.Model):
    MODE_CHOICES = [('practice', 'O\'rganish'), ('exam', 'Imtihon')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
 
class Answer(models.Model):
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1)
    is_correct = models.BooleanField()
    confidence = models.CharField(max_length=15, blank=True)   # 'ishonchli' / 'tахmin'
    time_spent_seconds = models.PositiveIntegerField(default=0)
Кейин моделларни маълумотлар базасига қўллаймиз:
Terminal
python manage.py makemigrations
python manage.py migrate
🎓 Ментордан маслаҳат
confidence майдонини эсдан чиқарма — бу ТЗ'нинг 6.1-бандидаги «Ишонч даражаси» (Confidence Calibration) функцияси учун асос. Кичик бир майдон, лекин келажакда «ишончли, лекин нотўғри» деган энг хавфли билим бўшлиқларини топишга ёрдам беради.
2-қадам. Admin panel — биринчи «ғалаба»
Django'нинг энг катта устунлиги — тайёр admin panel. Уни созлаш 5 дақиқа вақт олади, лекин сенга дарҳол маълумотлар билан ишлаш имконини беради (масалан, тест саволларини қўлда киритиш).
testengine/admin.py
# testengine/admin.py
from django.contrib import admin
from .models import Subject, Topic, Question, TestSession, Answer
 
admin.site.register(Subject)
admin.site.register(Topic)
admin.site.register(Question)
admin.site.register(TestSession)
admin.site.register(Answer)
Terminal
python manage.py createsuperuser
python manage.py runserver
Энди http://127.0.0.1:8000/admin манзилига кириб, биринчи фан ва саволларни қўлда қўша оласан. Бу — сенинг биринчи ишлаётган функционалинг!
3-қадам. Autentifikatsiya (OTP + JWT)
ТЗ'нинг 4.1-бандида айтилганидек, биз паролсиз, телефон рақами орқали OTP-асосидаги кириш қиламиз. Бу нафақат фойдаланувчи учун содда, балки хавфсизроқ ҳам — паролни ўғирлаш хавфи умуман йўқ.
3.1. Оддийлаштирилган оқим (MVP учун)
1.Фойдаланувчи телефон рақамини киритади → backend 4 xonali OTP kod generatsiya qiladi va SMS orqali yuboradi (yoki MVP bosqichida development uchun log'ga chiqaradi)
2.Фойдаланувчи OTP kodni kiritadi → backend tekshiradi
3.Agar to'g'ri bo'lsa → JWT access va refresh token qaytariladi
accounts/views.py
# accounts/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .otp import generate_otp, verify_otp   # o'zimiz yozadigan yordamchi funksiyalar
 
class RequestOTPView(APIView):
    def post(self, request):
        phone = request.data.get('phone_number')
        generate_otp(phone)   # SMS yuborish yoki dev rejimda log qilish
        return Response({'detail': 'OTP yuborildi'})
 
class VerifyOTPView(APIView):
    def post(self, request):
        phone = request.data.get('phone_number')
        code = request.data.get('code')
        if not verify_otp(phone, code):
            return Response({'detail': 'Kod noto\'g\'ri'}, status=400)
        user, _ = User.objects.get_or_create(phone_number=phone, defaults={'username': phone})
        tokens = RefreshToken.for_user(user)
        return Response({'access': str(tokens.access_token), 'refresh': str(tokens)})
⚠ Стажёрлар кўп йўл қўядиган хато
OTP кодни ҳеч қачон оддий матн (plain text) кўринишида, муддатсиз базада сақлама! OTP'ни Redis'да қисқа муддат (масалан, 5 дақиқа) билан сақла ва фойдаланилгандан сўнг дарҳол ўчир. Шунингдек, битта телефон рақами учун дақиқада нечта OTP so'ralishi mumkinligini чеклаш (rate limiting) — SMS xarajatini nazorat qilish uchun MUHIM.
4-қадам. Test Engine API — асосий функционал
Энди DRF (Django REST Framework) ёрдамида frontend билан «сўзлашадиган» API яратамиз. Аввал serializer — Python объектини JSON'га айлантирувчи қатлам.
4.1. Serializers
testengine/serializers.py
# testengine/serializers.py
from rest_framework import serializers
from .models import Question, TestSession, Answer
 
class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        # DIQQAT: correct_option maydonini frontendga YUBORMAYMIZ!
        fields = ['id', 'text', 'options', 'difficulty']
 
class AnswerSubmitSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_option = serializers.CharField(max_length=1)
    confidence = serializers.CharField(required=False)
    time_spent_seconds = serializers.IntegerField(default=0)
⚠ Стажёрлар кўп йўл қўядиган хато
Бу ТЗ'нинг талабларидаги энг критик хатолардан бири: QuestionSerializer'да correct_option майдонини фойдаланувчига юбориб юбориш! Агар шуни унутиб қўйсанг, ҳар қандай технологик билимли абитуриент browser'нинг Network бўлимидан тўғри жавобни кўриб олади. Ҳар доим fields рўйхатини ЭҲТИЁТКОРЛИК билан ёз — фақат керакли майдонларни кўрсат.
4.2. Views — тест бошлаш ва жавоб қабул қилиш
testengine/views.py
# testengine/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Question, TestSession, Answer, Subject
from .serializers import QuestionSerializer, AnswerSubmitSerializer
 
class StartTestView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        subject_id = request.data.get('subject_id')
        mode = request.data.get('mode', 'practice')
        session = TestSession.objects.create(
            user=request.user, subject_id=subject_id, mode=mode
        )
        questions = Question.objects.filter(topic__subject_id=subject_id).order_by('?')[:10]
        return Response({
            'session_id': session.id,
            'questions': QuestionSerializer(questions, many=True).data,
        })
 
class SubmitAnswerView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request, session_id):
        data = AnswerSubmitSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        question = Question.objects.get(id=data.validated_data['question_id'])
        is_correct = question.correct_option == data.validated_data['selected_option']
        Answer.objects.create(
            session_id=session_id,
            question=question,
            selected_option=data.validated_data['selected_option'],
            is_correct=is_correct,
            confidence=data.validated_data.get('confidence', ''),
            time_spent_seconds=data.validated_data['time_spent_seconds'],
        )
        # Frontend darhol izoh ko'rsata olishi uchun natijani qaytaramiz
        return Response({'is_correct': is_correct, 'correct_option': question.correct_option})
4.3. Соддалаштирилган адаптив мантиқ (MVP версияси)
ТЗ'нинг 4.2-бандида тавсифланган эвристик адаптацияни энди коdga айлантирамиз — кетма-кет 3 та тўғри жавобдан сўнг қийинлик даражасини оширамиз:
testengine/adaptive.py
# testengine/adaptive.py
def get_next_difficulty(session):
    """Oxirgi 3 ta javobga qarab keyingi savol qiyinligini aniqlaydi."""
    last_answers = session.answers.order_by('-id')[:3]
    if len(last_answers) < 3:
        return 3   # boshlang'ich, o'rtacha qiyinlik
    if all(a.is_correct for a in last_answers):
        current = last_answers[0].question.difficulty
        return min(current + 1, 5)   # qiyinlashtiramiz, lekin 5 dan oshmaydi
    if all(not a.is_correct for a in last_answers):
        current = last_answers[0].question.difficulty
        return max(current - 1, 1)   # osonlashtiramiz, lekin 1 dan pastga tushmaydi
    return last_answers[0].question.difficulty   # aralash natija — o'zgartirmaymiz
🎓 Ментордан маслаҳат
Диққат қил — бу функция жуда содда, лекин тўлиқ IRT алгоритмининг «руҳи»ни сақлайди: фойдаланувчи жавобига қараб қийинликни мослаштириш. ТЗ'да айтилганидек, тўлиқ IRT (Item Response Theory) моделини Phase 2'да қўшамиз — MVP'да мураккаб математикага ҳожат йўқ, содда эвристика етарли.
5-қадам. Натижа таҳлили
Тест тугагандан сўнг фойдаланувчига мавзу кесимидаги статистикани кўрсатиш керак. Бу — Django ORM'нинг aggregate функцияларини ўрганиш учун яхши амалиёт.
progress/services.py
# progress/services.py
from django.db.models import Count, Q
from testengine.models import Answer
 
def get_topic_breakdown(session):
    return (
        Answer.objects.filter(session=session)
        .values('question__topic__name')
        .annotate(
            total=Count('id'),
            correct=Count('id', filter=Q(is_correct=True)),
        )
    )
    # Natija: [{'question__topic__name': 'Kvadrat tenglamalar', 'total': 5, 'correct': 2}, ...]
•Нима учун services.py файли алоҳида: бу — Django'даги «fat models, thin views, business logic in services» тамойили. Мураккаб бизнес-мантиқни views.py'да эмас, алоҳида services.py'да ёзиш кодни тест қилишни ва қайта ишлатишни осонлаштиради.
6-қадам. Такрорлаш модули (FSRS — соддалаштирилган)
Бу — ТЗ'нинг 4.4-бандидаги «энг муҳим фарқловчи функция». Тўлиқ FSRS алгоритми мураккаб статистик формулаларга асосланади, лекин MVP учун унинг асосий ғоясини соддалаштирилган шаклда амалга оширамиз.
progress/models.py
# progress/models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta
 
class ReviewCard(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    question = models.ForeignKey('testengine.Question', on_delete=models.CASCADE)
    stability_days = models.FloatField(default=1.0)   # "eslab qolish kuchi"
    next_review_date = models.DateField(default=timezone.now)
 
    def update_after_review(self, was_correct: bool):
        """FSRS g'oyasining soddalashtirilgan versiyasi."""
        if was_correct:
            self.stability_days *= 2.2   # to'g'ri javob — interval kengayadi
        else:
            self.stability_days = max(self.stability_days * 0.5, 1)   # xato — interval qisqaradi
        self.next_review_date = timezone.now().date() + timedelta(days=round(self.stability_days))
        self.save()
🎓 Ментордан маслаҳат
Бу — «тўғри жавоб → узоқроқ кутиш, нотўғри жавоб → яқинроқ такрорлаш» деган FSRS'нинг асосий фалсафаси. Тўлиқ формула difficulty ва retrievability каби қўшимча параметрларни ҳам ҳисобга олади — буни Phase 2'да open-spaced-repetition кутубхонаси (py-fsrs) орқали жорий этиш тавсия этилади. Ҳозирча бу содда версия ҳам реал қиймат беради.
«Бугунги такрорлаш» рўйхатини олиш учун содда сўров:
progress/services.py
def get_today_review_cards(user):
    return ReviewCard.objects.filter(
        user=user, next_review_date__lte=timezone.now().date()
    ).select_related('question')
7-қадам. Gamification (Streak ва XP)
progress/models.py
# progress/models.py
class Streak(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    freezes_available = models.PositiveIntegerField(default=1)
 
    def register_activity(self):
        today = timezone.now().date()
        if self.last_activity_date == today:
            return   # bugun allaqachon faol bo'lgan
        yesterday = today - timedelta(days=1)
        if self.last_activity_date == yesterday:
            self.current_streak += 1          # ketma-ketlik davom etyapti
        elif self.last_activity_date and self.freezes_available > 0:
            self.freezes_available -= 1       # 'muz'dan foydalanib streak saqlanadi
            self.current_streak += 1
        else:
            self.current_streak = 1           # streak boshidan boshlanadi
        self.longest_streak = max(self.longest_streak, self.current_streak)
        self.last_activity_date = today
        self.save()
🎓 Ментордан маслаҳат
ТЗ'нинг 4.5-бандидаги «Streak Freeze» ғоясини кодга шундай татбиқ этамиз — фойдаланувчи бир кунни ўтказиб юборганда, агар «muz»и bo'lsa, streak yo'qolmaydi. Бу — жуда кичик код бўлаги, лекин ретеншнга катта таъсир қилади (изланишларимизда 14%гача D7 ретеншн ошиши кузатилган).
8-қадам. Тўлов интеграцияси (асосий тузилма)
MVP учун тўлов интеграциясининг тўлиқ коди провайдер (Payme/Click) ҳужжатларига қараб ёзилади, лекин архитектуравий тузилма қуйидагича бўлиши тавсия этилади:
billing/models.py
# billing/models.py
class Subscription(models.Model):
    STATUS_CHOICES = [('active', 'Faol'), ('expired', 'Muddati o\'tgan'), ('cancelled', 'Bekor qilingan')]
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    plan = models.CharField(max_length=50)         # masalan: 'monthly', 'quarterly'
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField()
 
class Payment(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    provider = models.CharField(max_length=20)     # 'payme' / 'click'
    provider_transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=15, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
⚠ Стажёрлар кўп йўл қўядиган хато
Тўлов провайдер webhook'ини ҳеч қачон текширмасдан ишончли деб қабул қилма! Payme/Click'дан келган ҳар бир сўровнинг imzosini (signature) провайдер ҳужжатларига қараб текшир, акс ҳолда исталган киши сохта «тўлов муваффақиятли» сўрови юбориб, бепул обуна ола олади.
9-қадам. AI интеграцияси (хато изоҳи)
ТЗ'нинг 10.1-бандидаги «Шахсийлаштирилган хато изоҳи» функциясини Anthropic Claude API орқали жорий этамиз. Диққат: арзон ва тезкор модел (масалан, Haiku даражасидаги) танланади ва натижа албатта кэшланади.
progress/ai_explainer.py
# progress/ai_explainer.py
import anthropic
from django.core.cache import cache
 
client = anthropic.Anthropic()   # API kalit muhit o'zgaruvchisidan olinadi
 
def explain_mistake(question_text, options, selected_option, correct_option):
    cache_key = f'explain:{hash(question_text)}:{selected_option}'
    cached = cache.get(cache_key)
    if cached:
        return cached   # avval so'ralgan — API'ga qayta murojaat qilmaymiz
 
    prompt = (
        f"Savol: {question_text}\nVariantlar: {options}\n"
        f"O'quvchi '{selected_option}' variantini tanladi, to'g'ri javob '{correct_option}'.\n"
        "O'quvchiga 2-3 gapda, sodda va rag'batlantiruvchi tilda, aynan shu xatoni tushuntir."
    )
    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=200,
        messages=[{'role': 'user', 'content': prompt}],
    )
    explanation = response.content[0].text
    cache.set(cache_key, explanation, timeout=60 * 60 * 24 * 30)   # 30 kunga keshlash
    return explanation
🎓 Ментордан маслаҳат
Кэшлашни (cache.set) ҳеч қачон унутма! Агар 1000 та фойдаланувчи бир хил саволда бир хил хато қилса, биз AI API'га 1000 марта эмас, БИР марта мурожаат қиламиз — бу ҳам xarajatni, ҳам javob vaqtini кескин камайтиради. ТЗ'нинг 10.3-бандидаги этик қоидага ҳам эътибор бер: AI изоҳи ҳеч қачон 'тўғри жавоб'ни ўзгартирмайди, фақат тушунтиради.
10-қадам. Тестлаш (pytest)
Ҳар бир жиддий Python лойиҳаси автоматик тестларга эга бўлиши шарт. Тест ёзиш — «ортиқча ишl» эмас, балки келажакда кодни бузмасдан ўзгартиришнинг ягона усули.
Terminal + testengine/tests/test_adaptive.py
pip install pytest pytest-django
 
# testengine/tests/test_adaptive.py
import pytest
from testengine.adaptive import get_next_difficulty
 
@pytest.mark.django_db
def test_difficulty_increases_after_three_correct(test_session_with_correct_answers):
    result = get_next_difficulty(test_session_with_correct_answers)
    assert result > 3   # qiyinlik oshgan bo'lishi kerak
•Нима учун бу муҳим: ТЗ'нинг 11.2-бандида айтилганидек, AI-агент ёзган ҳар қандай кодни автоматик тестлар орқали текшириш — «кўр-кўрона қабул қилиш»нинг олдини олади. Тест ёзишни ўрганиш — сенинг энг қимматли кўникмаларингдан бирига айланади.
11-қадам. Deployment асослари (Docker)
MVP'ни серверга чиқариш учун содда Docker конфигурацияси кифоя қилади:
Dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
🎓 Ментордан маслаҳат
Django'нинг ички dev server'и (`runserver`) ҳеч қачон production'да ишлатилмайди — у хавфсиз ва тезкор эмас. Production учун gunicorn (ёки uvicorn, agar async ishlatilsa) va nginx каби реал сервер воситалари ишлатилади.
Умумий кенгашлар ва якуний сўз
Тез-тез учрайдиган стажёр хатолари — умумлаштирилган рўйхат
•Хавфсиз бўлмаган майдонларни API'да очиб қўйиш: ҳар доим serializer'даги fields рўйхатини диққат билан текшир
•Migration'ларни унутиш: models.py'ни ўзгартиргандан сўнг ҳар доим makemigrations va migrate буйруқларини бажар
•Бизнес-мантиқни views.py'га «тиқиштириб» ёзиш: мураккаб логикани алоҳида services.py файлларида сақла
•Тест ёзмасдан «ишлайди» деб ҳисоблаш: қўлда бир марта синаб кўриш — тест эмас, автоматик тест доимий ишончни беради
•AI-генерация қилинган кодни тушунмасдан commit қилиш: ҳар доим кодни ўқиб, нима қилаётганини тушун
Ментордан якуний сўз
Бу қўлланма — сенинг йўл хаританг, лекин ягона тўғри йўл эмас. Дастурчилик — доимий ўрганиш жараёни, ва хатолар қилиш ўрганишнинг табиий қисми. Ҳар бир қадамни бажаргандан сўнг, ўзингдан сўра: «Мен нима учун бу қарорни қабул қилдим?» Агар жавоб бера олмасанг — қайтиб ортга бор ва тушун, кейин давом эт.
Омад тилайман — TestYourself'нинг биринчи ишлайдиган версиясини сен биргаликда қурасан!