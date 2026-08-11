# 📊 LOYIHA TAHLILI VA ETISHMAYOTGAN XUSUSIYATLAR
## DTM Test Platform - Toliq Sistemali Tavsif

---

## 🎯 LOYIHANING MAQSADI VA ASOSIY TUSHUNCHASI

**"TestYourself"** — bu **onlayn o'quv platforma** bo'lib, u quyidagi xususiyatlarga ega:
- **Talabalar** (studentlar) turli fanlarda testlarga javob berishlari
- **Google OAuth** orqali tizimga kirish
- **Test natijalarini** kuzatish va tahlil qilish
- **Subscription-based** biznes modeli (puli raqamlar uchun obuna)
- **XP va Streak** tizimi orqali talabalarni motivalashish
- **FSRS (Spaced Repetition) algoritmi** — takrorlash va eslab qolish sistemi

**Diqq at:** Bu faqat **Backend API** layeridagi Django loyihasi. Frontend (React/Vue) hali yaratilmagan.

---

## 📦 LOYIHANING TUZILISHI VA MODULLAR

### Hozirgi Modellar Tuzilishi:

```
┌─────────────────────────────────────────────────────────────┐
│                    ACCOUNT (Foydalanuvchi)                  │
├─────────────────────────────────────────────────────────────┤
│ • User (email, google_id, xp_total, role, full_name, ...)  │
│ • Rollari: STUDENT, MENTOR, ADMIN, SUPPORT                 │
└─────────────────────────────────────────────────────────────┘
            ▼
┌─────────────────────────────────────────────────────────────┐
│                  CATALOG (Test Tuzilishi)                   │
├─────────────────────────────────────────────────────────────┤
│ Subject (Fan)                                               │
│ ├── Topic (Mavzu)                                           │
│ │   └── Question (Savol)                                    │
│ │       ├── text (Savol matni)                              │
│ │       ├── options (JSON: {"A": "...", "B": "..."})       │
│ │       ├── correct_option ("A", "B", "C", "D")            │
│ │       └── difficulty (1-5: juda oson - juda qiyin)       │
│ │                                                           │
│ └── Subject → Multiple Topics                              │
│     (1 Subject'da ko'p Topic, 1 Topic'da ko'p Question)   │
└─────────────────────────────────────────────────────────────┘
            ▼
┌─────────────────────────────────────────────────────────────┐
│              TESTENGINE (Test Sessiyasi)                    │
├─────────────────────────────────────────────────────────────┤
│ • TestSession (User + Subject + Mode: PRACTICE/EXAM)       │
│ • Answer (Question va Javob ma'lumotlari)                  │
│ • TestResult (Test natijalari: score, correct/incorrect)   │
└─────────────────────────────────────────────────────────────┘
            ▼
┌─────────────────────────────────────────────────────────────┐
│              PROGRESS (Taraqqiyot Kuzatish)                 │
├─────────────────────────────────────────────────────────────┤
│ • ReviewCard (FSRS algoritmi - takrorlash qartasi)         │
│ • Streak (Ketma-ketlik: joriy, eng uzun)                   │
│ • XPTransaction (XP qo'shish/ayirish logi)                 │
└─────────────────────────────────────────────────────────────┘
            ▼
┌─────────────────────────────────────────────────────────────┐
│            BILLING (To'lovlar va Obuna)                     │
├─────────────────────────────────────────────────────────────┤
│ • Plan (Tarif: narxi, muddati)                              │
│ • Subscription (Foydalanuvchi obunasi: faol/tugadi/bekor)  │
│ • Payment (To'lovlar: Payme, Click, maqomi)                │
└─────────────────────────────────────────────────────────────┘
            ▼
┌─────────────────────────────────────────────────────────────┐
│            NOTIFICATIONS (Xabarlar va Eslatmalar)           │
├─────────────────────────────────────────────────────────────┤
│ • NotificationLog (SMS, Push xabarlar)                      │
│ • PushToken (FCM, APNS - mobile notifikaciyalar)           │
│ • ReminderSchedule (Takrorlash, Streak eslatmalari)        │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ HOZIRDA BOR XUSUSIYATLAR

### 1️⃣ TEST TUZILISHI (SUBJECT → TOPIC → QUESTION)
- ✅ **Subject (Fan)** — matematika, ingliz tili, fizika, kimyo
- ✅ **Topic (Mavzu)** — 1 fanning ichida mavzular (masalan: "Kvadrat tenglamalar", "Trigonometriya")
- ✅ **Question (Savol)** — har bir mavzuda savollar

**Hozirgi Tuzilish:**
```
Matematika (Subject)
├── Kvadrat tenglamalar (Topic 1)
│   ├── Savol 1
│   ├── Savol 2
│   └── ... (20-30 ta savol bo'lishi mumkin)
├── Trigonometriya (Topic 2)
│   ├── Savol 1
│   ├── Savol 2
│   └── ...
└── ... (10+ ta mavzu bo'lishi mumkin)
```

### 2️⃣ XP VA STREAK TIZIMI
- ✅ **XP (Experience Points)** — talabalar test yakunlaganda XP oladi
- ✅ **XPTransaction** — har bir XP o'zgarishi yoziladi (qaysi test, qancha XP)
- ✅ **Streak** — kunlik test ishlaganligi uchun ketma-ketlik (joriy va eng uzun)

### 3️⃣ FSRS ALGORITMI (Takrorlash Sistemi)
- ✅ **ReviewCard** — Spaced Repetition uchun savol kartasi
- ✅ **next_review_date** — keyingi takrorlash sanasi (hisob-kitob qiladi)
- ✅ **stability_days** — savol eslab qolish kuchi (1-dan ko'p kunga)

### 4️⃣ TEST SESSIYASI VA NATIJALAR
- ✅ **TestSession** — talaba test ishlaganda yaratiladi
- ✅ **Answer** — har bir savolga bergan javob
- ✅ **TestResult** — session yakunida: umumiy ball, to'g'ri/noto'g'ri sonlar

### 5️⃣ AUTHENTICATION (Autentifikatsiya)
- ✅ **Google OAuth** — telefon raqami emas, Google orqali kirish

---

## ❌ ETISHMAYOTGAN XUSUSIYATLAR (MUAMMO)

### 🔴 **1-MUAMMO: REYTING TIZIMI YO'Q (RATING SYSTEM)**

**Hozir nima bor?**
- Faqat **XP soni** bor (foydalanuvchi.xp_total)
- Faqat **Streak soni** bor (joriy ketma-ketlik)
- **Leaderboard** hech narsasi yo'q

**Nima kerak?**
Talabalarning reyting **4 ta darajada** hisob qilinishi kerak:

#### A) **DARSLIK REYTINGI** (Test Darajasi)
Har bir testdan keyin:
- ✅ To'g'ri javob = **+1 star** (yulduz)
- ❌ Noto'g'ri javob = **-0.5 star** (yoki 0 star)

**Misol:**
```
Test: "Kvadrat tenglamalar" (15 ta savol)
Talaba: 10 ta to'g'ri, 5 ta noto'g'ri

Reyting hisob-kitob:
- To'g'ri: 10 × 1 = 10 star
- Noto'g'ri: 5 × 0.5 = 2.5 star
- UMUMIY: 10 - 2.5 = 7.5 star ⭐⭐⭐⭐⭐⭐⭐ (7.5 / 15)
- FOIZ: 7.5 / 15 = 50% ✓
```

#### B) **MAVZU REYTINGI** (Topic Rating)
1 mavzudagi barcha testlar bo'yicha:
- Talaba "Kvadrat tenglamalar" mavzusida nechta testdan o'tdi?
- Har bitta testdan o'rtacha nechta yulduz oldi?
- **Mavzu reytingi** = Ushbu mavzudagi barcha testlardan o'rtacha yulduzlar

**Misol:**
```
"Kvadrat tenglamalar" mavzusida 3 ta test:
- Test 1: 7.5 star
- Test 2: 8 star
- Test 3: 6.5 star
- MAVZU REYTINGI: (7.5 + 8 + 6.5) / 3 = 7.33 star ⭐⭐⭐⭐⭐⭐⭐
```

#### C) **FAN REYTINGI** (Subject Rating)
1 fan bo'yicha barcha mavzularning o'rtacha reytingi:
- "Matematika" faning 10 ta mavzusi bo'yicha o'rtacha reyting

#### D) **UMUMIY TALABA REYTINGI** (Overall Rating)
Barcha fanlar bo'yicha o'rtacha reyting:
- Leaderboard'da birinchi o'rinda kim bor? (Eng yuqori reyting)

**HOZIR: Model yo'q, servicesi yo'q, API yo'q** ❌

---

### 🔴 **2-MUAMMO: DINAMIK REYTING O'ZGARISHI YO'Q**

**Nima kerak?**
Har safar talaba yangi test ishlaganda, barcha reytinglar yangilanishi kerak:
- Har test ishlaganda → talaba reytingi o'zgaradi (ko'taradi yoki tushadi)
- Mavzu reytingi o'zgaradi
- Fan reytingi o'zgaradi
- Umumiy leaderboard joylanishi o'zgaradi

**Misol:**
```
Bugun Asan:
- Matematika reytingi: 7.5 star
- Leaderboard: 10-o'rindi

Asan "Trigonometriya" testini ishlagani:
- 15 ta savol, 14 ta to'g'ri → 13.5 star ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐

Yangilangandan keyin:
- Matematika reytingi: (7.5 + 13.5) / 2 = 10.5 star (yuksaladi!)
- Leaderboard: 5-o'rindi (ko'tarildi!)
```

**HOZIR: Auto-calculation yo'q, update logikasi yo'q** ❌

---

### 🔴 **3-MUAMMO: KUN/HAFTA/OY/YILLIK REYTINGLAR YO'Q**

Talabalarni faqat **umumiy reyting** bo'yicha emas, balki **vaqtga qarab** kuzatish kerak:

```
┌─────────────────────────────────────────────────┐
│          REYTING TURLARISOVAY FORMATLARI        │
├─────────────────────────────────────────────────┤
│ • ALL TIME (Umumiy - hammasi)                   │
│ • YEARLY (Yillik - 2026 yil)                    │
│ • MONTHLY (Oylik - Dekabr 2025)                 │
│ • WEEKLY (Haftalik - 45-hafta)                  │
│ • DAILY (Kunlik - bugun ishlaganlari)           │
│ • HOURLY (Soatlik - oxirgi 1 soat)              │
└─────────────────────────────────────────────────┘
```

**Misol:**
```
Asan'ning reytingi:

BUGUN (Daily):
- 5 ta test ishlagani: 9.2 star ⭐⭐⭐⭐⭐⭐⭐⭐⭐
- Leaderboard: 3-o'rindi (bugun eng yaxshi)

BU HAFTA (Weekly):
- 28 ta test ishlagani: 8.5 star ⭐⭐⭐⭐⭐⭐⭐⭐⭐
- Leaderboard: 7-o'rindi

BU OY (Monthly):
- 120 ta test ishlagani: 7.8 star ⭐⭐⭐⭐⭐⭐⭐⭐
- Leaderboard: 15-o'rindi

UMUMIY (All Time):
- 450 ta test ishlagani: 7.3 star ⭐⭐⭐⭐⭐⭐⭐
- Leaderboard: 25-o'rindi
```

**HOZIR: Vaqt-asosli reytinglar yo'q** ❌

---

### 🔴 **4-MUAMMO: LEADERBOARD YO'Q**

**Nima kerak?**
Top-100 talabalarni ko'rsatadigan reytingli ro'yxat:

```
┌────────────────────────────────────────────────┐
│        🏆 LEADERBOARD - BUGUN (Daily)          │
├────────────────────────────────────────────────┤
│ 1. 🥇 Ali         - 9.8 star (32 test)         │
│ 2. 🥈 Fatima      - 9.6 star (28 test)         │
│ 3. 🥉 Asan        - 9.2 star (25 test)         │
│ 4.    Zara        - 8.9 star (24 test)         │
│ 5.    Javohir     - 8.7 star (22 test)         │
│ ...                                            │
│ 100.  Abdullayev  - 5.1 star (8 test)          │
└────────────────────────────────────────────────┘
```

**HOZIR: Leaderboard api'si yo'q, database model yo'q** ❌

---

### 🔴 **5-MUAMMO: REYTING TARIHCHASI YO'Q (Rating History)**

Talabaning reyting **qanday o'zgarganini** kuzatish kerak:

```
Asan'ning reyting tarixchasi:
- 2026-01-01: 5.0 star
- 2026-01-15: 6.2 star (↑1.2)
- 2026-02-01: 7.1 star (↑0.9)
- 2026-02-15: 7.5 star (↑0.4)
- 2026-03-01: 7.3 star (↓0.2)  [test ishlamadi]
- 2026-03-15: 8.1 star (↑0.8)  [ko'p test ishlagani]
```

**HOZIR: Tarikhiy ma'lumot saqlanmadi** ❌

---

### 🔴 **6-MUAMMO: KUZATUVCHI (OBSERVER) TIZIMI YO'Q**

**Ment va Adminlar talabalarni kuzatishlari kerak:**

```
MENTOR (Murabbiy) ko'rishi kerak:
├── Barcha talabalarining reytingi
├── Qaysi talabalar tushib bordi?
├── Qaysi talabalar yuksalmoqda?
├── Har bir talabaning detailed stats (qaysi mavzuda yomon?)
└── Alerts: "X talaba 3 kun test ishlamadi - eslatma yuborish kerak"

ADMIN ko'rishi kerak:
├── Umumiy platform statistikasi
├── Fan bo'yicha top-100 talaba
├── Xususiy ekranlar (analytics dashboard)
└── Birdan-bir tahlil
```

**HOZIR: Mentor/Admin dashboard yo'q** ❌

---

## 📊 HOZIRGI KODDA QANAQA REYTING MANTIQING BARCHALANSA?

### ✅ 1-QADAM: XP Transaction Model Bor
```python
# progress/models.py
class XPTransaction(BaseModel):
    user = ForeignKey('account.User')
    amount = IntegerField()           # XP miqdori
    source = CharField(choices=[TEST, STREAK, REVIEW, BONUS])
    description = CharField()
```
- **Maqsadi:** Har bir XP o'zgarishi yoziladi
- **Muammo:** Faqat XP soni, reyting yo'q

### ✅ 2-QADAM: TestResult Model Bor
```python
# testengine/models.py
class TestResult(BaseModel):
    session = OneToOneField(TestSession)
    total_score = PositiveIntegerField()
    correct_count = PositiveIntegerField()
    incorrect_count = PositiveIntegerField()
    duration_seconds = PositiveIntegerField()
```
- **Maqsadi:** Test natijalarini saqla
- **Muammo:** Reyting hisob-kitob qilmadi

### ✅ 3-QADAM: Streak Model Bor
```python
# progress/models.py
class Streak(BaseModel):
    user = OneToOneField('account.User')
    current_streak = PositiveIntegerField()
    longest_streak = PositiveIntegerField()
    last_activity_date = DateField()
```
- **Maqsadi:** Kunlik ketma-ketlik kuzatish
- **Muammo:** Faqat ketma-ketlik, reyting yo'q

### ❌ YO'QTASI:
```
1. ❌ Rating model (yulduzlar saqlanadigan model)
2. ❌ Leaderboard (top-100 talabalar)
3. ❌ Rating history (reyting qanday o'zgarganini yozish)
4. ❌ Daily/Weekly/Monthly calculations
5. ❌ Rating calculation service/logic
6. ❌ Auto-update mechanisms (har test ishlaganda avtomatik yangilash)
```

---

## 🛠 ETISHMAYOTGAN TEXNOLOJI VA API ENDPOINTLARI

### Database Models (Kerak):
```python
# 1. Rating Model (Yulduzlar)
class Rating(BaseModel):
    user = ForeignKey(User)
    topic = ForeignKey(Topic)
    stars = FloatField(0.0 - 5.0)  # 1-5 yulduz
    test_count = PositiveIntegerField()
    correct_count = PositiveIntegerField()
    updated_at = DateTimeField()

# 2. UserStats (Vaqt-asosli statistika)
class UserStats(BaseModel):
    user = ForeignKey(User)
    period = CharField(['daily', 'weekly', 'monthly', 'yearly', 'all_time'])
    stars = FloatField()
    tests_completed = PositiveIntegerField()
    streak = PositiveIntegerField()
    rank = PositiveIntegerField()
    date = DateField()

# 3. Leaderboard (Reytingli ro'yxat)
class Leaderboard(BaseModel):
    period = CharField()  # 'daily', 'weekly', etc.
    rank = PositiveIntegerField()
    user = ForeignKey(User)
    stars = FloatField()
    tests_completed = PositiveIntegerField()
    last_updated = DateTimeField()

# 4. RatingHistory (Reyting tarihchasi)
class RatingHistory(BaseModel):
    user = ForeignKey(User)
    previous_stars = FloatField()
    new_stars = FloatField()
    change = FloatField()  # +0.5, -0.2, etc.
    reason = CharField()  # Savol to'g'ri, mavzu o'rtacha, etc.
    date = DateTimeField(auto_now_add=True)
```

### API Endpoints (Kerak):
```
GET  /api/ratings/user/me/                   → Mening reyting
GET  /api/ratings/user/{id}/                 → Boshqa talabaning reyting
GET  /api/ratings/topics/{topic_id}/         → Bir mavzudagi reytinglar
GET  /api/ratings/subjects/{subject_id}/     → Bir fanning reytinglari

GET  /api/leaderboard/daily/                 → Kunlik top-100
GET  /api/leaderboard/weekly/                → Haftalik top-100
GET  /api/leaderboard/monthly/               → Oylik top-100
GET  /api/leaderboard/all_time/              → Umumiy top-100

GET  /api/stats/user/me/?period=daily        → Mening statistika (kunlik/haftalik/oylik)
GET  /api/stats/history/?days=30             → Reyting tarixchasi (oxirgi 30 kun)

GET  /api/dashboard/mentor/                  → Mentor uchun dashboard
GET  /api/dashboard/admin/                   → Admin uchun dashboard
```

---

## 🔄 REYTING HISOB-KITOB FORMULAR (ALGORITM)

```
BOSQICH 1: Test Natijasindan Yulduzlar Hisob Qilish
════════════════════════════════════════════════════

FormulaUnus:
    Yulduzlar = (Tog'ri Javoblar / Umumiy Savollar) × 5

Misol:
    Test: 15 ta savol
    Tog'ri: 12 ta
    Yulduzlar = (12 / 15) × 5 = 4.0 ⭐⭐⭐⭐

ADVANCED:
    Yulduzlar = (Tog'ri × 1 - Notog'ri × 0.5) / Umumiy Savollar × 5
    
    Misol:
        Tog'ri: 10 × 1 = 10
        Notog'ri: 5 × 0.5 = 2.5
        (10 - 2.5) / 15 × 5 = 7.5 / 15 × 5 = 2.5 ⭐⭐⭐


BOSQICH 2: Mavzu Reytingi (Topic Rating)
════════════════════════════════════════════════════

FormulaUnus:
    Mavzu Reytingi = Ushbu Mavzudagi Barcha Testlarning Yulduzlari / Test Soni

Misol:
    "Kvadrat tenglamalar" mavzusida 5 ta test:
    Test 1: 4.0 yulduz
    Test 2: 3.5 yulduz
    Test 3: 4.5 yulduz
    Test 4: 3.8 yulduz
    Test 5: 4.2 yulduz
    
    Mavzu Reytingi = (4.0 + 3.5 + 4.5 + 3.8 + 4.2) / 5 = 4.0 ⭐⭐⭐⭐


BOSQICH 3: Fan Reytingi (Subject Rating)
════════════════════════════════════════════════════

FormulaUnus:
    Fan Reytingi = Ushbu Fanning Barcha Mavzularining O'rtacha Reytingi

Misol:
    "Matematika" faning 10 ta mavzusi:
    Mavzu 1: 4.0
    Mavzu 2: 3.8
    Mavzu 3: 4.2
    ... (10 ta jami)
    
    Fan Reytingi = (4.0 + 3.8 + ... + X) / 10 = 3.95 ⭐⭐⭐⭐


BOSQICH 4: Umumiy Talaba Reytingi (Overall Rating)
════════════════════════════════════════════════════

FormulaUnus:
    Umumiy Reytingi = Barcha Fanlarining O'rtacha Reytingi

Misol:
    Talaba 5 ta fan o'qiyapti:
    Matematika: 4.0
    Ingliz tili: 3.8
    Fizika: 3.5
    Kimyo: 3.9
    Biologiya: 4.1
    
    Umumiy Reytingi = (4.0 + 3.8 + 3.5 + 3.9 + 4.1) / 5 = 3.86 ⭐⭐⭐⭐


BOSQICH 5: Vaqt-Asosli Reytinglar (Time-based Ratings)
════════════════════════════════════════════════════════

Har bir vaqt davrida (kun, hafta, oy, yil) alohida reytinglar hisob qilinadi.

Kunlik Reytingi = Bugun ishlagani test yulduzlarining o'rtachasi
Haftalik Reytingi = Bu haftada ishlagani barcha testlar yulduzlarining o'rtachasi
Oylik Reytingi = Bu oy ishlagani barcha testlar yulduzlarining o'rtachasi
```

---

## 📋 QANDAY QO'SHIMCHA XUSUSIYATLAR KERAK EKAN?

### ✅ Kerak bo'lgan Narsalar (Priority Tartibida):

| # | Nomi | Tavsifi | Qiyinlik | Vaqt |
|---|------|---------|---------|------|
| 1 | **Rating Model va Logic** | Yulduz hisob-kitob sistemi | 🔴 High | 8 soat |
| 2 | **Leaderboard API** | Top-100 talabalar | 🟡 Medium | 6 soat |
| 3 | **UserStats Model** | Vaqt-asosli statistika | 🟡 Medium | 8 soat |
| 4 | **Auto-update Service** | Test yakunida reyting yangilash | 🔴 High | 10 soat |
| 5 | **Rating History** | Reyting tarixchasi | 🟡 Medium | 5 soat |
| 6 | **Mentor Dashboard** | Barcha talabalar statistikasi | 🟢 Low | 12 soat |
| 7 | **Daily/Weekly/Monthly** | Vaqt-asosli leaderboard | 🟡 Medium | 8 soat |
| 8 | **Rating Aggregation** | Fan/Mavzu reytinglarini hisob-kitob | 🔴 High | 10 soat |

---

## 📝 HOZIRDA ISHLAB TURILAYOTGAN NARSALAR

### ✅ CORE API Endpoints (50% tayyor):
- [x] Authentication (Google OAuth)
- [x] Test Session API
- [x] Answer API
- [x] TestResult API
- [ ] **Rating API** ← KERAK
- [ ] **Leaderboard API** ← KERAK
- [ ] **Stats API** ← KERAK

### ✅ Frontend Integration (0% - yo'q):
- [ ] React/Vue frontend
- [ ] Quiz UI components
- [ ] Rating display
- [ ] Leaderboard UI
- [ ] Mentor dashboard

### ✅ Admin Panel (30% tayyor):
- [x] Django Admin (Unfold)
- [ ] Advanced analytics
- [ ] Custom reports
- [ ] User management dashboard

---

## 💡 XULOSA VA TAVSIYALAR

### Muammo:
- **Loyihada test tuzilishi bor** (Subject → Topic → Question) ✅
- **Loyihada XP va Streak bor** ✅
- **LEKIN: Reyting (rating) sistemi yo'q** ❌

### Kerak bo'lgan Qo'shimchalar:
1. **Rating Model** — Yulduzlar va reytinglar saqlanadigan database
2. **Rating Calculation Service** — Har test yakunida yulduzlar hisob-kitob qilish
3. **Leaderboard** — Top-100 talabalar ko'rsatish
4. **Time-based Stats** — Kunlik/haftalik/oylik reytinglar
5. **Mentor Dashboard** — Talabalarni kuzatish
6. **Auto-update Mechanism** — Reyting avtomatik yangilash

### Taxminiy Baholash:
- **Development vaqti:** 5-7 hafta (50+ soat kod yozish)
- **Testing vaqti:** 2-3 hafta
- **Deployment:** 1 hafta

### Keyingi Qadam:
1. Rating model yaratish (database schema)
2. Rating calculation service yaratish (business logic)
3. API endpoints yaratish (REST API)
4. Leaderboard service yaratish
5. Frontend integration qilish

---

## 📚 QO'SHIMCHA FAYDALANUVCHI (USTOZ) QO'SHISH IMKONIYATI

**Hozirda nima bor?**
- User roles: STUDENT, MENTOR, ADMIN, SUPPORT ✅

**Qanday topsirilgan?**
```python
# account/models.py
role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
```

**Muammo:**
- MENTOR rollari hali API'sida IMPLEMENTATION qilinmagan
- Mentor o'z talabalarini ko'rish uchun API yo'q
- Mentor hisobi / Talabani birlashtirishning logikasi yo'q

**Kerak bo'lgan Narsalar:**
- Mentor-Talaba bog'lanish (Many-to-Many model)
- Mentor Dashboard API
- Mentor analytics endpoints
- Mentor notifications (qaysi talaba past reyting, qaysi yaxshi, etc.)

---

## 🎯 YAKUNIY XULOSA

| Komponent | Status | Catego Izoh |
|-----------|--------|-----------|
| **Test Tuzilishi** | ✅ Tayyor | Subject → Topic → Question |
| **XP Tizimi** | ✅ Tayyor | XPTransaction model + logic |
| **Streak** | ✅ Tayyor | Kunlik ketma-ketlik kuzatish |
| **FSRS Algoritm** | ✅ Tayyor | ReviewCard model + takrorlash sana |
| **Authentication** | ✅ Tayyor | Google OAuth + JWT |
| **Billing** | ✅ Tayyor | Plan, Subscription, Payment models |
| **Notifications** | ✅ Tayyor | NotificationLog, PushToken |
| **TEST ENGINE** | ✅ Tayyor | TestSession, Answer, TestResult |
| **RATING SYSTEM** | ❌ **YO'Q** | 🔴 PRIORITY: Yulduzlar, leaderboard, reytinglar |
| **LEADERBOARD** | ❌ **YO'Q** | 🔴 PRIORITY: Top-100 talabalar |
| **TIME-BASED STATS** | ❌ **YO'Q** | 🟡 MEDIUM: Kunlik/haftalik reytinglar |
| **MENTOR DASHBOARD** | ❌ **YO'Q** | 🟡 MEDIUM: Talabalarni kuzatish |
| **ADMIN ANALYTICS** | ⏳ 30% | 🟡 MEDIUM: Statslar va tahlil |
| **Frontend** | ❌ **YO'Q** | 🟢 LOW: React/Vue UI |

---

**✍️ Tayyorlagan:** Backend Tahlil Tizim | **📅 Sana:** 2026-08-11
