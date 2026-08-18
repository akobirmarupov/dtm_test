# 📚 DTM TEST - LOYIHA TO'LIQ DOKUMENTATSIYASI

**Loyiha nomi:** TestYourself (O'zingizni Sinovdan O'tkazing)  
**Dastur tili:** Python (Django REST Framework)  
**Maqsadi:** Online o'quvchilar uchun test platformasi + ustuvor (mentor) tizimi + o'qish rivojlanishni kuzatish

---

## 📋 MUNDARIJA
1. [Loyiha Tuzilishi](#loyiha-tuzilishi)
2. [Rollar va Huquqlar](#rollar-va-huquqlar)
3. [Real Hayot Ssenari](#real-hayot-ssenari)
4. [API Dokumentatsiyasi](#api-dokumentatsiyasi)
5. [Data Modellar](#data-modellar)
6. [Tugmalar va Faoliyatlar](#tugmalar-va-faoliyatlar)

---

## 🏗️ LOYIHA TUZILISHI

```
dtm_test/
├── account/           ← Autentifikatsiya va foydalanuvchi profili
├── catalog/           ← Fanlar, mavzular, savollar
├── testengine/        ← Test sessiyalari va javoblar
├── progress/          ← O'qish progressing, streak, XP, takrorlash
├── billing/           ← To'lov va obuna
├── notifications/     ← SMS, Push bildirishnomalar
├── common/            ← Umumiy permissions, pagination, throttle
└── config/            ← Asosiy sozlamalar
```

---

## 👥 ROLLAR VA HUQUQLAR

### 1. **STUDENT (Talaba)** - O'QUVCHI
**Nima qilishi mumkin:**
- ✅ Google orqali ro'yxatdan o'tish va kirish
- ✅ Test yechish (Practice mode va Exam mode)
- ✅ O'z natijalarini ko'rish
- ✅ O'qish streakini ko'rish
- ✅ Savollarni takrorlash (FSRS spaced repetition)
- ✅ XP (ballar) yig'ish
- ✅ Obuna sotib olish va to'lov qilish

**Nima qila olmaydi:**
- ❌ Boshqa talabalarning natijalarini o'zgartirish
- ❌ Fanlar qo'shish
- ❌ Adminiy funksiyalar

---

### 2. **MENTOR (Usta/Murabbiy)** - USTOZLIK
**Nima qilishi mumkin:**
- ✅ Talabalarni o'rganish
- ✅ Talabalarning progress-ini kuzatish
- ✅ Talabalarning ichi o'tkazgan savollarini ko'rish
- ✅ Maslahat berish
- ✅ Talabalarning natijalarini talhlil qilish

**Nima qila olmaydi:**
- ❌ To'lovlarni boshqarish
- ❌ Fanlarni o'zgartirish
- ❌ Boshqa mentorlari boshqarish

---

### 3. **ADMIN (Administrator)** - BOSH MENEJER
**Nima qilishi mumkin:**
- ✅ Foydalanuvchilarni boshqarish (Create, Read, Update, Delete)
- ✅ Fanlar, mavzular, savollarni qo'shish/o'zgartirish/o'chirish
- ✅ To'lov rejalarini yaratish va boshqarish
- ✅ Barcha talabalarning natijalarini ko'rish
- ✅ System statistikasini ko'rish
- ✅ Django Admin paneli orqali boshqarish

**Nima qila olmaydi:**
- ❌ Talabalarning passwordlarini o'zgartirish (faqat reset)
- ❌ Tizim qiyofasini o'zgartirish

---

### 4. **SUPPORT (Qo'llab-Quvvatlash)** - CUSTOMER SERVICE
**Nima qilishi mumkin:**
- ✅ Talabalardan so'rovlarga javob berish
- ✅ To'lov masalalarini hal qilish
- ✅ Talabalarning account muammolarini tahlil qilish

---

## 🎬 REAL HAYOT SSENARI

### SSENARI 1: YANGI FOYDALANUVCHI GOOGLE ORQALI RO'YXATDAN O'TADI

```
1️⃣ Foydalanuvchi "Google orqali kirish" tugmasini bosadi
   ↓
2️⃣ Frontend Google Login SDK-ni chaqiradi
   ↓
3️⃣ Google ID token backend-ga yuboriladi
   ↓
4️⃣ Backend Google token-ni tekshiradi (verify_google_token)
   ↓
5️⃣ Agar email yangi bo'lsa:
   - Yangi User create qilinadi
   - Role: STUDENT (standart)
   ↓
6️⃣ JWT access_token va refresh_token generate qilinadi
   ↓
7️⃣ Frontend barcha API-larni access_token bilan chaqiradi
```

**API Endpoint:**
```
POST /api/auth/google/
Body: {
  "id_token": "GOOGLE_ID_TOKEN"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Abdulla Qodirov",
    "role": "student",
    "xp_total": 0
  },
  "is_new_user": true
}
```

---

### SSENARI 2: TALABA TEST YECHADI

```
1️⃣ Talaba "Test yechish" tugmasini bosadi
   ↓
2️⃣ Frontend "Fanni tanlang" dialoqini ko'rsatadi
   ↓
3️⃣ Talaba "Matematika" fanini tanlaydi
   ↓
4️⃣ Backend Test Session create qiladi (Practice mode)
   ↓
5️⃣ Frontend test sessiyani oladi, birinchi savolni ko'rsatadi
   ↓
6️⃣ Talaba javob tanlaydi (A, B, C yoki D)
   ↓
7️⃣ Javob backend-ga yuboriladi:
   POST /testengine/sessions/1/answers/
   {
     "question_id": 5,
     "selected_option": "A",
     "confidence": "sure"  // yoki "guess"
   }
   ↓
8️⃣ Backend:
   - Answer yozuvini create qiladi
   - To'g'ri/noto'g'ri tekshiradi
   - Agar to'g'ri bo'lsa: XP qo'shadi (+10 XP)
   ↓
9️⃣ Keyingi savolga o'tadi (GET /testengine/sessions/1/next-question/)
   ↓
🔟 Barcha savollarni yechgandan so'ng:
   POST /testengine/sessions/1/finish/
   ↓
1️⃣1️⃣ Backend TestResult create qiladi:
   - Umumiy ball
   - To'g'ri/noto'g'ri soni
   - Vaqti
   - ReviewCard-larni yaratadi (keyingi takrorlash uchun)
   - Streak-ni yangilaydi
```

**API Endpoints:**
```
GET /testengine/sessions/          # Barcha test sessiyalarini ko'rish
POST /testengine/sessions/         # Yangi test session yaratish
GET /testengine/sessions/1/        # Test session detallari
POST /testengine/sessions/1/next-question/   # Keyingi savol
POST /testengine/sessions/1/answers/         # Javob berish
POST /testengine/sessions/1/finish/          # Test tugash
GET /testengine/results/           # Barcha natijalar
GET /testengine/results/my-results/ # O'z natijalarim
```

---

### SSENARI 3: STREAK (KETMA-KETLIK)

```
📅 DAY 1 (Dushanba): Talaba test yechdi
   ✅ Streak: 1 kun ✓

📅 DAY 2 (Seshanba): Talaba test yechdi
   ✅ Streak: 2 kun ✓

📅 DAY 3 (Chorshanba): Talaba test YO'Q yechdi
   ❌ Streak uzildi: 0 kun

🆘 FAQAT 1 MARTA "MUZ" ISHLATISH MUMKIN:
   - Freeze tugmasini bosish
   - Streak uzilishi rad etiladi
   - Freeze = 0 bo'ladi
   - Keyingi freeze faqat premium obuna bilan qo'shiladi
```

**API Endpoints:**
```
GET /progress/streak/              # Streakni ko'rish
POST /progress/streak/freeze/      # Freeze ishlatish
```

---

### SSENARI 4: REVIEW (TAKRORLASH) - FSRS ALGORITMI

```
📖 FSRS (Free Spaced Repetition System):
   - Har bir savol qayta takrorlash uchun optimal vaqt hisoblanadi
   - Agar to'g'ri yechsan → keyingi 3 kun
   - Agar noto'g'ri yechsan → keyingi 1 kun

1️⃣ Talaba takorlash ro'yxatini ko'rish:
   GET /progress/reviews/today/
   
   Response:
   [
     {
       "id": 1,
       "question": {"id": 5, "text": "2+2=?"},
       "next_review_date": "2026-08-11",
       "stability_days": 3.0
     }
   ]

2️⃣ Talaba takrorlash savolini yechadi:
   POST /progress/reviews/1/submit/
   {
     "is_correct": true,
     "confidence": "sure"
   }

3️⃣ Backend next_review_date-ni qayta hisobla va saqladi
```

**API Endpoints:**
```
GET /progress/reviews/             # Barcha review kartalari
GET /progress/reviews/today/       # Bugun takrorlash kerak bo'lgan
POST /progress/reviews/1/submit/   # Takrorlash yechildi
```

---

### SSENARI 5: XP VA LEADERBOARD

```
XP MANBALARI:
┌─────────────────────────────────────┐
│ Test test yakunlash    → +10 XP     │
│ To'g'ri javob           → +5 XP     │
│ Streak (har kun)        → +2 XP     │
│ Takrorlash               → +1 XP     │
│ Bonus (admin)            → +N XP     │
└─────────────────────────────────────┘

1️⃣ Talaba test yechdi va 8 ta to'g'ri javob berdi:
   +10 (sessiya) + 8*5 (to'g'ri) + 2 (streak) = +52 XP
   
2️⃣ XP transaction saqlandi
   
3️⃣ Weekly leaderboard yangilandi

4️⃣ API-dan ko'rish:
   GET /progress/xp/summary/
   
   Response:
   {
     "xp_total": 1250,
     "xp_today": 52,
     "xp_week": 300
   }
   
   GET /progress/leaderboard/weekly/
   
   Response:
   [
     {"rank": 1, "user": "Ali", "xp": 500},
     {"rank": 2, "user": "Vali", "xp": 450},
     {"rank": 3, "user": "Sohib", "xp": 400}
   ]
```

**API Endpoints:**
```
GET /progress/xp/transactions/         # Barcha XP tranzaksiyalar
GET /progress/xp/summary/              # Umumiy XP statistika
GET /progress/leaderboard/weekly/      # Haftalik reyting
```

---

### SSENARI 6: OBUNA VA TO'LOV

```
1️⃣ Talaba "Premium obuna" tugmasini bosadi
   ↓
2️⃣ Frontend obuna rejalarini ko'rsatadi:
   - Oyna (Free)
   - Oy (2,99$)
   - Yillik (29,99$)
   ↓
3️⃣ Talaba "Oy" rejasini tanlayd
   ↓
4️⃣ Frontend to'lov tizimini (Payme/Click) chaqiradi
   ↓
5️⃣ To'lov ko'rsatuladi va talaba amalga oshiradi
   ↓
6️⃣ Backend to'lov statusini kuzatib turadi:
   POST /billing/payments/
   {
     "plan_id": 2,
     "provider": "payme",
     "amount": 2.99
   }
   ↓
7️⃣ To'lov muvaffaqiyatli bo'lsa:
   - Subscription create qilinadi (expires_at: 30 kundan keyin)
   - Payment status = "success"
   - Premium features unlock
   ↓
8️⃣ Premium features:
   ✅ Cheksiz streak freeze (kunlik 3 ta)
   ✅ Exam mode (imtihon rejimi)
   ✅ Savollar analitikasi
   ✅ Mentor taklifi
```

**API Endpoints:**
```
GET /billing/plan/                 # Barcha rejalar
POST /billing/subscriptions/       # Yangi obuna
GET /billing/subscriptions/current/ # Joriy obuna
POST /billing/subscriptions/1/cancel/  # Obunani bekor qilish
POST /billing/payments/            # To'lov qilish
POST /billing/payments/1/approve/  # To'lovni tasdiqlash (Admin)
POST /billing/payments/1/reject/   # To'lovni rad etish (Admin)
```

---

## 📡 API DOKUMENTATSIYASI

### 🔑 AUTENTIFIKATSIYA (Account)

#### 1. **Google orqali kirish**
```
POST /api/auth/google/

Body:
{
  "id_token": "GOOGLE_ID_TOKEN"
}

Response (201 Created):
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Abdulla Qodirov",
    "avatar_url": "https://...",
    "role": "student",
    "xp_total": 0
  },
  "is_new_user": true
}
```

#### 2. **O'z profili ko'rish**
```
GET /api/auth/me/

Headers:
Authorization: Bearer {access_token}

Response (200 OK):
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Abdulla Qodirov",
  "role": "student",
  "xp_total": 1250,
  "region": "Tashkent",
  "target_major": "Computer Science",
  "consent_share_with_universities": true
}
```

#### 3. **Tizimdan chiqish (Logout)**
```
POST /api/auth/logout/

Headers:
Authorization: Bearer {access_token}

Body:
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response (200 OK):
{
  "detail": "Tizimdan muvaffaqiyatli chiqdingiz"
}
```

#### 4. **Token yangilash**
```
POST /api/auth/refresh/

Body:
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response (200 OK):
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### 📚 KATALOG (Fanlar, Mavzular, Savollar)

#### 1. **Fanlarni ko'rish (Paginated)**
```
GET /catalog/subjects/?page=1&page_size=20

Response (200 OK):
{
  "count": 50,
  "next": "http://api/catalog/subjects/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Matematika",
      "created_at": "2026-01-01T10:00:00Z",
      "updated_at": "2026-08-01T15:30:00Z"
    },
    {
      "id": 2,
      "name": "Fizika",
      "created_at": "2026-01-01T10:05:00Z",
      "updated_at": "2026-08-01T16:00:00Z"
    }
  ]
}
```

#### 2. **Fan qo'shish (Admin)**
```
POST /catalog/subjects/

Headers:
Authorization: Bearer {access_token}

Body:
{
  "name": "Kimyo"
}

Response (201 Created):
{
  "id": 3,
  "name": "Kimyo",
  "created_at": "2026-08-10T12:00:00Z",
  "updated_at": "2026-08-10T12:00:00Z"
}
```

#### 3. **Fan o'zgartirish (Admin)**
```
PUT /catalog/subjects/1/

Headers:
Authorization: Bearer {access_token}

Body:
{
  "name": "Yuqori Matematika"
}

Response (200 OK):
{
  "id": 1,
  "name": "Yuqori Matematika"
}
```

#### 4. **Fan o'chirish (Admin)**
```
DELETE /catalog/subjects/1/

Response (204 No Content)
```

#### 5. **Mavzualarni ko'rish**
```
GET /catalog/topics/?subject_id=1&page=1

Response (200 OK):
{
  "results": [
    {
      "id": 1,
      "name": "Sonlar va operatsiyalar",
      "subject_id": 1
    },
    {
      "id": 2,
      "name": "Tenglamalar",
      "subject_id": 1
    }
  ]
}
```

#### 6. **Savollarni ko'rish**
```
GET /catalog/questions/?topic_id=1&difficulty=3&page=1

Query params:
- topic_id: Mavzu ID
- difficulty: 1-5 (Juda oson dan Juda qiyin)
- page: Sahifa raqami

Response (200 OK):
{
  "results": [
    {
      "id": 5,
      "text": "2+2 ning qiymati qanday?",
      "options": {
        "A": "3",
        "B": "4",
        "C": "5",
        "D": "6"
      },
      "correct_option": "B",
      "difficulty": 1,
      "topic_id": 1
    }
  ]
}
```

#### 7. **Savol qo'shish (Admin)**
```
POST /catalog/questions/

Headers:
Authorization: Bearer {access_token}

Body:
{
  "topic_id": 1,
  "text": "3+3 ning qiymati qanday?",
  "options": {
    "A": "5",
    "B": "6",
    "C": "7",
    "D": "8"
  },
  "correct_option": "B",
  "difficulty": 1
}

Response (201 Created):
{
  "id": 100,
  "text": "3+3 ning qiymati qanday?",
  ...
}
```

---

### 🧪 TEST ENGINE (Test Sessiyalari, Javoblar, Natijalar)

#### 1. **Test sessiyasini yaratish**
```
POST /testengine/sessions/

Headers:
Authorization: Bearer {access_token}

Body:
{
  "subject_id": 1,
  "mode": "practice"  // yoki "exam"
}

Response (201 Created):
{
  "id": 42,
  "user_id": 1,
  "subject_id": 1,
  "mode": "practice",
  "started_at": "2026-08-10T12:00:00Z",
  "finished_at": null
}
```

#### 2. **Test sessiyalarni ko'rish**
```
GET /testengine/sessions/?page=1

Response (200 OK):
{
  "results": [
    {
      "id": 42,
      "user_id": 1,
      "subject": {
        "id": 1,
        "name": "Matematika"
      },
      "mode": "practice",
      "started_at": "2026-08-10T12:00:00Z",
      "finished_at": null
    }
  ]
}
```

#### 3. **Sessiya detallari**
```
GET /testengine/sessions/42/

Response (200 OK):
{
  "id": 42,
  "user_id": 1,
  "subject": {
    "id": 1,
    "name": "Matematika"
  },
  "mode": "practice",
  "started_at": "2026-08-10T12:00:00Z",
  "finished_at": null,
  "answers_count": 3,
  "result": null  // Sessiya tugamaganiga,
}
```

#### 4. **Keyingi savol olish**
```
GET /testengine/sessions/42/next-question/

Response (200 OK):
{
  "question": {
    "id": 5,
    "text": "2+2 ning qiymati qanday?",
    "options": {
      "A": "3",
      "B": "4",
      "C": "5",
      "D": "6"
    },
    "difficulty": 1,
    "topic": {
      "id": 1,
      "name": "Sonlar va operatsiyalar"
    }
  },
  "question_number": 1,
  "total_questions": 20
}
```

#### 5. **Javob berish**
```
POST /testengine/sessions/42/answers/

Headers:
Authorization: Bearer {access_token}

Body:
{
  "question_id": 5,
  "selected_option": "B",
  "confidence": "sure"  // yoki "guess"
}

Response (201 Created):
{
  "id": 1,
  "session_id": 42,
  "question_id": 5,
  "selected_option": "B",
  "is_correct": true,
  "confidence": "sure",
  "time_spent_seconds": 15,
  "created_at": "2026-08-10T12:05:00Z"
}
```

#### 6. **Javoblarni bulk qo'shish (mobile sync)**
```
POST /testengine/sessions/42/answers/bulk/

Body:
{
  "answers": [
    {
      "question_id": 5,
      "selected_option": "B",
      "confidence": "sure",
      "time_spent_seconds": 15
    },
    {
      "question_id": 6,
      "selected_option": "C",
      "confidence": "guess",
      "time_spent_seconds": 30
    }
  ]
}

Response (201 Created):
{
  "created": 2,
  "failed": 0
}
```

#### 7. **Test tugash**
```
POST /testengine/sessions/42/finish/

Response (200 OK):
{
  "message": "Test muvaffaqiyatli tugadi",
  "result": {
    "id": 1,
    "session_id": 42,
    "total_score": 95,
    "correct_count": 19,
    "incorrect_count": 1,
    "duration_seconds": 1800
  }
}
```

#### 8. **Natijalarni ko'rish**
```
GET /testengine/results/?page=1

Response (200 OK):
{
  "results": [
    {
      "id": 1,
      "session": {
        "id": 42,
        "subject": "Matematika"
      },
      "total_score": 95,
      "correct_count": 19,
      "incorrect_count": 1,
      "duration_seconds": 1800,
      "created_at": "2026-08-10T12:30:00Z"
    }
  ]
}
```

#### 9. **O'z natijalarim**
```
GET /testengine/results/my-results/

Response (200 OK):
{
  "results": [
    {
      "id": 1,
      "total_score": 95,
      "correct_count": 19,
      ...
    }
  ]
}
```

---

### 📈 PROGRESS (Streak, XP, ReviewCard)

#### 1. **Streakni ko'rish**
```
GET /progress/streak/

Headers:
Authorization: Bearer {access_token}

Response (200 OK):
{
  "id": 1,
  "user_id": 1,
  "current_streak": 7,
  "longest_streak": 15,
  "last_activity_date": "2026-08-10",
  "freezes_available": 1
}
```

#### 2. **Freeze ishlatish**
```
POST /progress/streak/freeze/

Headers:
Authorization: Bearer {access_token}

Response (200 OK):
{
  "id": 1,
  "user_id": 1,
  "current_streak": 7,  // Freezdan keyin o'zgarmadi
  "freezes_available": 0  // Kamaydi
}

Error Response (400 Bad Request):
{
  "detail": "Sizda ishlatish uchun 'muz' qolmagan."
}
```

#### 3. **Bugun takrorlash kerak bo'lgan savollar**
```
GET /progress/reviews/today/

Headers:
Authorization: Bearer {access_token}

Response (200 OK):
{
  "results": [
    {
      "id": 1,
      "question": {
        "id": 5,
        "text": "2+2=?"
      },
      "stability_days": 3.0,
      "next_review_date": "2026-08-13"
    }
  ]
}
```

#### 4. **Barcha review kartalari**
```
GET /progress/reviews/

Response (200 OK):
{
  "results": [
    {
      "id": 1,
      "question_id": 5,
      "stability_days": 3.0,
      "next_review_date": "2026-08-13"
    }
  ]
}
```

#### 5. **Takrorlash yechildi**
```
POST /progress/reviews/1/submit/

Headers:
Authorization: Bearer {access_token}

Body:
{
  "is_correct": true,
  "confidence": "sure"
}

Response (200 OK):
{
  "id": 1,
  "question_id": 5,
  "stability_days": 6.0,  // Yangi qiymat
  "next_review_date": "2026-08-16"  // Yangi sana
}
```

#### 6. **XP statistikasi**
```
GET /progress/xp/summary/

Headers:
Authorization: Bearer {access_token}

Response (200 OK):
{
  "xp_total": 1250,
  "xp_today": 52,
  "xp_week": 300,
  "xp_month": 1000
}
```

#### 7. **XP tranzaksiyalari**
```
GET /progress/xp/transactions/?page=1

Response (200 OK):
{
  "results": [
    {
      "id": 1,
      "user_id": 1,
      "amount": 10,
      "source": "test",
      "description": "Test yakunlandi",
      "created_at": "2026-08-10T12:00:00Z"
    },
    {
      "id": 2,
      "user_id": 1,
      "amount": 5,
      "source": "test",
      "description": "To'g'ri javob",
      "created_at": "2026-08-10T12:05:00Z"
    }
  ]
}
```

#### 8. **Haftalik Leaderboard**
```
GET /progress/leaderboard/weekly/

Response (200 OK):
{
  "results": [
    {
      "rank": 1,
      "user": {
        "id": 5,
        "full_name": "Ali Abdurahmon",
        "avatar_url": "https://..."
      },
      "xp": 500,
      "streak": 7
    },
    {
      "rank": 2,
      "user": {
        "id": 3,
        "full_name": "Vali Valiyev",
        "avatar_url": "https://..."
      },
      "xp": 450,
      "streak": 5
    }
  ]
}
```

---

### 💳 BILLING (To'lov va Obuna)

#### 1. **Barcha obuna rejalarini ko'rish**
```
GET /billing/plan/

Response (200 OK):
{
  "results": [
    {
      "id": 1,
      "name": "Free",
      "price": "0.00",
      "duration_days": 999999,
      "is_active": true
    },
    {
      "id": 2,
      "name": "Monthly",
      "price": "2.99",
      "duration_days": 30,
      "is_active": true
    },
    {
      "id": 3,
      "name": "Yearly",
      "price": "29.99",
      "duration_days": 365,
      "is_active": true
    }
  ]
}
```

#### 2. **Yangi obuna qo'shish (To'lov oldidan)**
```
POST /billing/subscriptions/

Headers:
Authorization: Bearer {access_token}

Body:
{
  "plan_id": 2
}

Response (201 Created):
{
  "id": 1,
  "user_id": 1,
  "plan_id": 2,
  "status": "active",
  "starts_at": "2026-08-10T12:00:00Z",
  "expires_at": "2026-09-10T12:00:00Z"
}
```

#### 3. **Joriy obunani ko'rish**
```
GET /billing/subscriptions/current/

Headers:
Authorization: Bearer {access_token}

Response (200 OK):
{
  "id": 1,
  "user_id": 1,
  "plan": {
    "id": 2,
    "name": "Monthly",
    "price": "2.99"
  },
  "status": "active",
  "starts_at": "2026-08-10T12:00:00Z",
  "expires_at": "2026-09-10T12:00:00Z",
  "days_remaining": 31
}
```

#### 4. **Obunani bekor qilish**
```
POST /billing/subscriptions/1/cancel/

Headers:
Authorization: Bearer {access_token}

Response (200 OK):
{
  "id": 1,
  "status": "cancelled",
  "expires_at": "2026-09-10T12:00:00Z"
}
```

#### 5. **To'lov qilish**
```
POST /billing/payments/

Headers:
Authorization: Bearer {access_token}

Body:
{
  "subscription_id": 1,
  "provider": "payme",
  "amount": "2.99"
}

Response (201 Created):
{
  "id": 1,
  "user_id": 1,
  "subscription_id": 1,
  "provider": "payme",
  "provider_transaction_id": "TXN123456",
  "amount": "2.99",
  "status": "pending"
}
```

#### 6. **To'lovni tasdiqlash (Admin)**
```
POST /billing/payments/1/approve/

Headers:
Authorization: Bearer {access_token}

Response (200 OK):
{
  "id": 1,
  "status": "success",
  "subscription": {
    "status": "active"
  }
}
```

#### 7. **To'lovni rad etish (Admin)**
```
POST /billing/payments/1/reject/

Headers:
Authorization: Bearer {access_token}

Response (200 OK):
{
  "id": 1,
  "status": "failed"
}
```

---

## 📊 DATA MODELLAR

### User Model
```python
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Abdulla Qodirov",
  "google_id": "1234567890",
  "avatar_url": "https://...",
  "role": "student",  # student, mentor, admin, support
  "region": "Tashkent",
  "target_major": "Computer Science",
  "xp_total": 1250,
  "consent_share_with_universities": true,
  "is_active": true,
  "is_staff": false,  # Admin qo'p uchun
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-08-10T12:00:00Z"
}
```

### TestSession Model
```python
{
  "id": 42,
  "user_id": 1,
  "subject_id": 1,
  "mode": "practice",  # practice yoki exam
  "started_at": "2026-08-10T12:00:00Z",
  "finished_at": "2026-08-10T12:30:00Z",  # Faqat tugaganidan keyin
  "created_at": "2026-08-10T12:00:00Z",
  "updated_at": "2026-08-10T12:30:00Z"
}
```

### Answer Model
```python
{
  "id": 1,
  "session_id": 42,
  "question_id": 5,
  "selected_option": "B",
  "is_correct": true,
  "confidence": "sure",  # sure yoki guess
  "time_spent_seconds": 15,
  "created_at": "2026-08-10T12:05:00Z",
  "updated_at": "2026-08-10T12:05:00Z"
}
```

### TestResult Model
```python
{
  "id": 1,
  "session_id": 42,
  "total_score": 95,  # 0-100
  "correct_count": 19,
  "incorrect_count": 1,
  "duration_seconds": 1800,  # 30 daqiqa
  "created_at": "2026-08-10T12:30:00Z",
  "updated_at": "2026-08-10T12:30:00Z"
}
```

### Streak Model
```python
{
  "id": 1,
  "user_id": 1,
  "current_streak": 7,  # Joriy ketma-ketlik kunlari
  "longest_streak": 15,  # Eng uzun ketma-ketlik
  "last_activity_date": "2026-08-10",
  "freezes_available": 1,  # Mavjud "muzlar"
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-08-10T12:00:00Z"
}
```

### ReviewCard Model
```python
{
  "id": 1,
  "user_id": 1,
  "question_id": 5,
  "stability_days": 3.0,  # FSRS algoritmi
  "next_review_date": "2026-08-13",
  "created_at": "2026-08-01T10:00:00Z",
  "updated_at": "2026-08-10T12:00:00Z"
}
```

### XPTransaction Model
```python
{
  "id": 1,
  "user_id": 1,
  "amount": 10,
  "source": "test",  # test, streak, review, bonus
  "description": "Test yakunlandi",
  "created_at": "2026-08-10T12:00:00Z",
  "updated_at": "2026-08-10T12:00:00Z"
}
```

### Subscription Model
```python
{
  "id": 1,
  "user_id": 1,
  "plan_id": 2,
  "status": "active",  # active, expired, cancelled
  "starts_at": "2026-08-10T12:00:00Z",
  "expires_at": "2026-09-10T12:00:00Z",
  "created_at": "2026-08-10T12:00:00Z",
  "updated_at": "2026-08-10T12:00:00Z"
}
```

### Payment Model
```python
{
  "id": 1,
  "user_id": 1,
  "subscription_id": 1,
  "provider": "payme",  # payme yoki click
  "provider_transaction_id": "TXN123456",
  "amount": "2.99",
  "status": "success",  # pending, success, failed
  "created_at": "2026-08-10T12:00:00Z",
  "updated_at": "2026-08-10T12:05:00Z"
}
```

---

## 🔘 TUGMALAR VA FAOLIYATLAR

### STUDENT (O'QUVCHI) TUGMALARI

| Tugma | Nomi | API | Chiqarish |
|-------|------|-----|----------|
| 🔐 | Google orqali kirish | POST /api/auth/google/ | Access token, Refresh token |
| 👤 | Profil ko'rish | GET /api/auth/me/ | Foydalanuvchi ma'lumotlari |
| 🚪 | Chiqish | POST /api/auth/logout/ | "Muvaffaqiyatli chiqdingiz" |
| 📚 | Fanlarni ko'rish | GET /catalog/subjects/ | Fanlar ro'yxati |
| 📖 | Test yechish | POST /testengine/sessions/ | Test session ID |
| ❓ | Savol olish | GET /testengine/sessions/42/next-question/ | Savol va variantlar |
| ✍️ | Javob berish | POST /testengine/sessions/42/answers/ | Javob ID, to'g'ri/noto'g'ri |
| ✅ | Test tugash | POST /testengine/sessions/42/finish/ | Test Result |
| 📊 | Natijalarni ko'rish | GET /testengine/results/my-results/ | Barcha natijalar |
| 🔥 | Streakni ko'rish | GET /progress/streak/ | Joriy/eng uzun streak |
| ❄️ | Freezni ishlatish | POST /progress/streak/freeze/ | Streak saqlandi |
| 📋 | Takrorlashni ko'rish | GET /progress/reviews/today/ | Takrorlash ro'yxati |
| 🎯 | Takrorlash yechish | POST /progress/reviews/1/submit/ | Keyingi sanasi |
| 💰 | XP ko'rish | GET /progress/xp/summary/ | Umumiy XP |
| 🏆 | Leaderboard | GET /progress/leaderboard/weekly/ | Top 100 |
| 💳 | Obuna rejalarini ko'rish | GET /billing/plan/ | Plan ro'yxati |
| 🛍️ | Obuna sotib olish | POST /billing/subscriptions/ | Subscription ID |
| 💵 | To'lov qilish | POST /billing/payments/ | Payment ID |

### MENTOR (USTOZLIK) TUGMALARI

| Tugma | Nomi | API | Chiqarish |
|-------|------|-----|----------|
| 👥 | Talabalarni o'rganish | GET /testengine/results/ | Barcha natijalar |
| 📈 | Talabaning progress | GET /testengine/results/my-results/ | Talabaning natijalar |
| ❓ | Talabaning javoblar | GET /testengine/sessions/42/ | Session detallari |
| 📊 | Streak analitikasi | GET /progress/streak/ | Streak ma'lumotlar |

### ADMIN (ADMINISTRATOR) TUGMALARI

| Tugma | Nomi | API | Chiqarish |
|-------|------|-----|----------|
| 👨‍💼 | Foydalanuvchilarni boshqarish | GET/POST/PUT/DELETE /admin/ | User CRUD |
| 📚 | Fanlar qo'shish/o'zgartirish | POST/PUT/DELETE /catalog/subjects/ | Subject CRUD |
| 📖 | Mavzular qo'shish/o'zgartirish | POST/PUT/DELETE /catalog/topics/ | Topic CRUD |
| ❓ | Savollar qo'shish/o'zgartirish | POST/PUT/DELETE /catalog/questions/ | Question CRUD |
| 💰 | Obuna rejalarini yaratish | POST /billing/plan/ | Plan ID |
| 💳 | To'lovlarni tasdiqlash/rad etish | POST /billing/payments/1/approve/ | Payment status |
| 📊 | Statistika ko'rish | GET /testengine/results/ | Barcha natijalar |

---

## 🔒 AUTHENTICATION VA PERMISSIONS

### JWT Token Flow:
```
Frontend         Backend           Database
   |                |                 |
   |--Google ID---->|                 |
   |                |---Verify token--|
   |                |<--Valid user----|
   |                |                 |
   |                |--Generate JWT---|
   |<--Access Token-|                 |
   |<--Refresh Token|                 |
   |                |                 |

Keyingi requestlarda:
   |--GET /api/auth/me/-->|
   |   Authorization: Bearer <access_token>
   |                |--Verify token--|
   |                |<--User valid---|
   |                |--Return data---|
   |<--User data----| 
```

### Permission Levels:
- **AllowAny**: Hech kim (Google login)
- **IsAuthenticated**: Faqat tizimga kirgan foydalanuvchilar
- **IsStudent**: Faqat "student" rolidagi foydalanuvchilar
- **IsMentor**: Faqat "mentor" rolidagi foydalanuvchilar
- **IsAdmin**: Faqat "admin" rolidagi foydalanuvchilar

---

## 🚀 REAL HAYOT ISHLASH JARAYONI

### 1. APP OYNANGANDA:
```
Boshlash → Google Login → User Create/Login → Home Screen
           ↓
        Token Save → API Calls with JWT
```

### 2. TEST YECHGANDA:
```
Test Tanlash → Session Create → Questions Loop
                                ↓
                        Answer Save → Check Correct
                                ↓
                        XP Add → Next Question
                                ↓
                        Test Finish → Result Create
                                ↓
                        ReviewCards Create
```

### 3. DAILY WORKFLOW:
```
Morning: Check Streak (Are you still active?)
           ↓ Yes
        ReviewCards (Takrorlash)
           ↓
        Do Test
           ↓
        Get XP
           ↓
Evening: Check Leaderboard
```

---

## ⚙️ TECHNICAL DETAILS

### Throttling (API Limit):
- **Anonimlar**: 20 request/minut
- **Foydalanuvchilar**: 100 request/minut
- **Admin**: Cheksiz

### Pagination:
- Default page size: 20
- Max page size: 100
- `?page=1&page_size=50`

### Cache:
- Streak: 5 daqiqa
- Leaderboard: 1 soat

### Database Relations:
```
User 1 ──── ∞ TestSession ──── ∞ Answer ──── 1 Question
 ∞           ∞          │
 │           │          └──── 1 TestResult
 │           └──── 1 Subject
 │
 ├─── 1 Streak
 ├─── ∞ ReviewCard ─── 1 Question
 ├─── ∞ XPTransaction
 ├─── ∞ Subscription ─── 1 Plan
 ├─── ∞ Payment
 └─── ∞ NotificationLog
```

---

## 📞 ERROR CODES

| Kod | Nomi | Sababi |
|-----|------|--------|
| 200 | OK | Muvaffaqiyatli |
| 201 | Created | Yangi object create qilindi |
| 400 | Bad Request | Noto'g'ri ma'lumot |
| 401 | Unauthorized | Token yo'q yoki eskirgan |
| 403 | Forbidden | Huquq yo'q |
| 404 | Not Found | Object topilmadi |
| 500 | Server Error | Server xatosi |

---

## 🎓 KEYINGI QADAMLAR (TO'LIQLASHTIRISH)

### Joriy Holat:
- ✅ Authentication (Google OAuth)
- ✅ Test Engine API
- ✅ Progress tracking
- ✅ Billing models

### Qo'shilishi Kerak:
- ⏳ Notifications (SMS/Push)
- ⏳ Admin Dashboard
- ⏳ Frontend (React/Vue.js)
- ⏳ Mobile App (Flutter/React Native)
- ⏳ Analytics
- ⏳ Mentor Dashboard
- ⏳ Email Notifications

---

**Tayyor juda! 🎉 Endi Figma-ga qarab shunday UI yasashingiz mumkin!**
