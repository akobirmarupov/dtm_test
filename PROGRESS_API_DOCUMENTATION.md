# 📚 PROGRESS APP - FRONTEND DOKUMENTATSIYASI

## 🎯 ASOSIY MAQSAD
Talabalarning o'quv rivojlanishini kuzatish va motivalashish tizimi. Talabalar:
- Savollarni takrorlash va o'qish
- XP yig'ish va leaderboard'da reyting olish
- Ketma-ketlik (Streak) saqlash
- Bugun takrorlash kerak bo'lgan savollarni ko'rish

---

## 🔗 API ENDPOINTLAR VA FRONTEND INTEGRATIONS

### 1️⃣ REVIEWCARD (TAKRORLASH QARTASI) APIs

#### 📋 **API 1: Barcha ReviewCard Kartalarini Olish**

**Endpoint:**
```
GET http://localhost:8000/progress/reviews/
```

**Headers:**
```
Authorization: Bearer YOUR_JWT_ACCESS_TOKEN
Content-Type: application/json
```

**Query Parameters (optional):**
```
?page=1
?user=5
?question=12
?stability_days_min=1.0
?stability_days_max=5.0
?next_review_date=2026-08-09
?next_review_date_after=2026-08-01
?next_review_date_before=2026-08-31
```

**Response (200 OK):**
```json
{
  "count": 42,
  "next": "http://localhost:8000/progress/reviews/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "question": 5,
      "question_text": "O'smanli imperiyasi qachon tuzildi?",
      "subject_name": "Tarix",
      "topic_name": "Ortaasrlar",
      "stability_days": 3.5,
      "next_review_date": "2026-08-12"
    },
    {
      "id": 2,
      "question": 7,
      "question_text": "Genessa shartnomasi qachon imzolandi?",
      "subject_name": "Tarix",
      "topic_name": "Zamonaviy tarix",
      "stability_days": 1.0,
      "next_review_date": "2026-08-10"
    }
  ]
}
```

**Nima uchun kerak?**
- Talabaning **BARCHA takrorlash kartalarini** ko'rsatish
- Filterlash: Stability, sana, savol bo'yicha
- **Sahifalanish:** Page 1, 2, 3... (har sahifada 20-30 ta)

**Frontend'da ishlatish:**
```javascript
// Savollarni listga ko'rsatish
// Filterlash (topiklik, sanadlik)
// Pagination - "Keyingi sahifa" tugmasi
// Har kartada: Savol metni, subject, qachon takrorlash
```

**Cache:** ❌ Cache yo'q (har quyidirilib keladi)

---

#### 📋 **API 2: Bugun Takrorlash Kerak Bo'lgan Kartalar**

**Endpoint:**
```
GET http://localhost:8000/progress/reviews/today/
```

**Headers:**
```
Authorization: Bearer YOUR_JWT_ACCESS_TOKEN
Content-Type: application/json
```

**Response (200 OK):**
```json
{
  "count": 8,
  "results": [
    {
      "id": 2,
      "question": 7,
      "question_text": "Genessa shartnomasi qachon imzolandi?",
      "subject_name": "Tarix",
      "topic_name": "Zamonaviy tarix",
      "stability_days": 1.0,
      "next_review_date": "2026-08-09"
    },
    {
      "id": 5,
      "question": 12,
      "question_text": "Rossiya inqilob yili?",
      "subject_name": "Tarix",
      "topic_name": "Zamonaviy tarix",
      "stability_days": 2.0,
      "next_review_date": "2026-08-09"
    }
  ]
}
```

**Nima uchun kerak?**
- **BUGUN takrorlash kerak bo'lgan** savollarni ko'rsatish
- `next_review_date <= bugun`
- Talaba ochgan vaqtda "Bugun 8 ta savol bor!" demasi
- **Cache:** 5 minut (tezraq yuklash)

**Frontend'da ishlatish:**
```javascript
// App'ni ochgan vaqtda:
// - "Bugun {count} ta savol bor"
// - Birinchi sahifada BUGUNGI savollarni ko'rsatish
// - "Start Review" tugmasi
// - Har savol: Quiz-ga o'tish
```

**Cache Qanday Ishlaydi:**
```
1. Talaba 13:00'da app ochdi -> API chaqirish -> Cache qilindi
2. Talaba 13:02'da yangi tartibni chaqirdi -> Cache'dan olish (2 minut o'tgan)
3. Talaba 13:06'da (5 minut o'tgani bilan) -> Cache yangilandi
```

---

#### 📋 **API 3: Savolga Javob Berish (Eng Muhim!)**

**Endpoint:**
```
POST http://localhost:8000/progress/reviews/{id}/submit/
```

**Path Parameter:**
```
{id} = ReviewCard ID (Misol: 2, 5, 12, ...)
```

**Headers:**
```
Authorization: Bearer YOUR_JWT_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body (JSON):**
```json
{
  "is_correct": true,
  "response_time": 45
}
```

**Request Body Qoidalari:**
- `is_correct`: BOOLEAN (`true` yoki `false`)
  - `true` = Javob to'g'ri
  - `false` = Javob noto'g'ri
- `response_time`: INTEGER (soniyalarda)
  - Minimum: 0
  - Maksimum: 3600 (1 soat)
  - Misol: 45 = 45 sekund

**Response (200 OK):**
```json
{
  "id": 2,
  "question": 7,
  "question_text": "Genessa shartnomasi qachon imzolandi?",
  "subject_name": "Tarix",
  "topic_name": "Zamonaviy tarix",
  "stability_days": 2.0,
  "next_review_date": "2026-08-10"
}
```

**Nima bo'layotgani Backend'da:**

✅ **Agar `is_correct: true`:**
```
1. stability_days OSHADI: 1.0 -> 2.0 -> 4.0 -> 8.0 ...
   Formulasi: stability_days * 2.0
   
2. next_review_date hisoblandi:
   Bugun (2026-08-09) + 2.0 kun = 2026-08-11
   
3. XPTransaction yaratiladi:
   amount = 50 XP, source = "review"
   
4. Talaba's rank'i ko'tariladi!
```

❌ **Agar `is_correct: false`:**
```
1. stability_days KAMAYADI: 3.0 -> 1.5 -> 0.75...
   Formulasi: max(1.0, stability_days * 0.5)
   Eng kam 1.0 kun (qayta sodir bo'lmaslik uchun)
   
2. next_review_date yangilandi:
   Bugun (2026-08-09) + 1.0 kun = 2026-08-10
   
3. XPTransaction yaratiladi:
   amount = -10 XP, source = "review"
   
4. Leaderboard'da ko'tarilmaydi
```

**Frontend'da ishlatish:**
```javascript
// Quiz'da:
// 1. Savol ko'rsatildi, timer boshlanadi
// 2. Talaba javob berdi (yoki shunga qarang)
// 3. Timer to'xtadi - response_time = timer value
// 4. Javobni tekshir (API yoki frontend?)
// 5. SUBMIT:
//    POST /reviews/{id}/submit/
//    { is_correct: true/false, response_time: 45 }
// 6. Response'dan yangi stability_days olish
// 7. "✅ To'g'ri! Keyingi takrorlash 11-august"
//    yoki
//    "❌ Noto'g'ri! Keyingi takrorlash 10-august"
```

**Cache Tozalash:**
```
Bu API chaqirilganida:
1. ReviewCard'ni yangilash
2. Cache DELETE: 'progress:reviews:today:user:{user_id}'
3. Keyingi GET /reviews/today/ yangi ma'lumot qaytaradi
```

---

### 2️⃣ STREAK (KETMA-KETLIK) APIs

#### 📊 **API 4: Streak Holati Ko'rish**

**Endpoint:**
```
GET http://localhost:8000/progress/streak/
```

**Headers:**
```
Authorization: Bearer YOUR_JWT_ACCESS_TOKEN
Content-Type: application/json
```

**Response (200 OK):**
```json
{
  "current_streak": 45,
  "longest_streak": 120,
  "last_activity_date": "2026-08-09",
  "freezes_available": 1
}
```

**Ma'lumotlar Tushuntirishi:**

| Field | Nima | Misol |
|-------|------|-------|
| `current_streak` | Hozir ketma-ketlik (kunlar) | 45 = 45 kun takrorlash qilgan |
| `longest_streak` | Eng uzun ketma-ketlik | 120 = Eng ko'pi 120 kun bo'lgan |
| `last_activity_date` | Oxirgi faollik sanasi | 2026-08-09 = Bugun harakat qilgan |
| `freezes_available` | Qolgan "muz" soni | 1 = 1 marta ishlatish mumkin |

**Frontend'da ishlatish:**
```javascript
// Home Page'da "Profile" ko'rsatish:
// 🔥 STREAK: 45 kun
// 🏆 Best: 120 kun
// ❄️ Freezes: 1 mavjud
// 
// Eger last_activity_date != bugun bo'lsa:
// OGOHLANTIRISH: "Siz bugun harakat qilmadingiz!"
```

**Cache:** ✅ Cache 5 minut

**Shunday bo'lishi kerak:**
```
Har har kun:
1. Test yoki Review qilsa
2. Streak +1
3. Uchrakmasa
4. Streak 0 ga o'tadi (HANGAT FREEZE qo'llanmasa)
```

---

#### ❄️ **API 5: Muz Ishlatish (Freeze)**

**Endpoint:**
```
POST http://localhost:8000/progress/streak/freeze/
```

**Headers:**
```
Authorization: Bearer YOUR_JWT_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```
BO'YIN BO'LADI! (Empty body)
```

**Response (200 OK):**
```json
{
  "current_streak": 45,
  "longest_streak": 120,
  "last_activity_date": "2026-08-09",
  "freezes_available": 0
}
```

**Nima bo'layotgani Backend'da:**

**✅ Muz Ishlatilganida:**
```
1. freezes_available: 1 -> 0 (kamayadi)
2. last_activity_date: YANGILANDI (bugun deb saqlandi)
3. current_streak: SAQLANADI! (uzilib ketmadi)
4. next kun test/review qilmasa ham +1 kun streak qo'shilib qoladi

Misol:
- Juma: 45 kun streak
- Shanba: Muz ishlatdi
- Yakshanba: Test/Review qilmasa: 46 kun (uzilib ketmadi!)
```

**❌ Muz Yo'q Bo'lsa Error:**
```json
{
  "detail": "Sizda ishlatish uchun 'muz' qolmagan."
}
```

**Frontend'da ishlatish:**
```javascript
// Streak Ko'rsatilgan Joyida:
// 
// if (freezes_available > 0) {
//   "🧊 FREEZE ISHLATISH" tugmasi (Aktiv)
// } else {
//   "❄️ Muz yo'q" (O'chirilgan)
// }
//
// Tugmasini bosganida:
// Confirmation: "Muz ishlatmoqchisiz? Streak saqlanadi!"
// POST /streak/freeze/
// Response: "✅ Muz ishlatildi! Keyingi hafta yangilandi."
```

**Muz Qayta Yangilanishi:**
```
Default: 1 ta muz/hafta
Dushanba ⏰: freezes_available = 1 (yangilandi)
Shanba: Muz ishlatildi -> freezes_available = 0
Yakshanba: Dushanba ⏰ bo'lguncha = 0
Dushanba: freezes_available = 1 (qayta yangilandi)
```

---

### 3️⃣ XP VA LEADERBOARD APIs

#### 💰 **API 6: XP Tranzaksiyalar (Tarixi)**

**Endpoint:**
```
GET http://localhost:8000/progress/xp/transactions/
```

**Headers:**
```
Authorization: Bearer YOUR_JWT_ACCESS_TOKEN
Content-Type: application/json
```

**Query Parameters (optional):**
```
?page=1
?user=5
?source=review
?source=test
?source=streak
?source=bonus
```

**Response (200 OK):**
```json
{
  "count": 156,
  "next": "http://localhost:8000/progress/xp/transactions/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "amount": 50,
      "source": "review",
      "source_display": "Takrorlash",
      "description": "ReviewCard #2 to'g'ri javob",
      "created_at": "2026-08-09T13:45:30Z"
    },
    {
      "id": 2,
      "amount": 5,
      "source": "streak",
      "source_display": "Streak",
      "description": "45 kun streak bonus",
      "created_at": "2026-08-09T08:00:00Z"
    },
    {
      "id": 3,
      "amount": 75,
      "source": "test",
      "source_display": "Test yakunlandi",
      "description": "Test Session #1 - 90% to'g'ri",
      "created_at": "2026-08-08T16:20:15Z"
    }
  ]
}
```

**XP Source Turlarini Tushuntirishi:**

| Source | Nom | Nima | Miqdori |
|--------|-----|------|---------|
| `review` | Takrorlash | ReviewCard to'g'ri javob | 50 XP |
| `test` | Test | Testni yakunlash | 50-100 XP |
| `streak` | Streak | Ketma-ketlik bonusi | 5 XP/kun |
| `bonus` | Bonus | Admin'dan bonus | Ixtiyoriy |

**Frontend'da ishlatish:**
```javascript
// "Tarixim" sahifasida:
// XP Tarihini ko'rsatish
// Recent: Eng yaqinda oligan XP
// Filter: Source bo'yicha filterlash
// Pagination: Eski XP'larni ko'rish

// Har transaction'da:
// - Icon (review/test/streak/bonus)
// - "+50 XP" yoki "+75 XP"
// - "Review - Takrorlash" (source_display)
// - "13:45" (vaqti)
// - Green (bonus) yoki Blue (regular)
```

**Cache:** ❌ Cache yo'q

---

#### 📊 **API 7: XP Xulosa (Summary)**

**Endpoint:**
```
GET http://localhost:8000/progress/xp/summary/
```

**Headers:**
```
Authorization: Bearer YOUR_JWT_ACCESS_TOKEN
Content-Type: application/json
```

**Response (200 OK):**
```json
{
  "xp_total": 2450,
  "xp_today": 125,
  "xp_this_week": 680
}
```

**Ma'lumotlar Tushuntirishi:**

| Field | Nima | Misol |
|-------|------|-------|
| `xp_total` | Jami XP (boshidan bugun'gacha) | 2450 = Umumiy reyting |
| `xp_today` | Bugungi XP | 125 = Bugun 125 XP olingan |
| `xp_this_week` | Bu hafta XP | 680 = Dushanba'dan shugacha |

**Frontend'da ishlatish:**
```javascript
// Dashboard'da ko'rsatiladi:
// 
// 🏆 SHURINGIZ STATISTIKASI
// 💎 Jami XP: 2450
// 🌟 Bugun: +125 XP
// 📈 Bu hafta: +680 XP
//
// Animatsiya: Raqamlar oshganida animation
// Color: Green (yangi XP)
```

**Cache:** ✅ Cache 5 minut

---

#### 🏆 **API 8: Haftalik Leaderboard (Reyting)**

**Endpoint:**
```
GET http://localhost:8000/progress/leaderboard/weekly/
```

**Headers:**
```
Authorization: Bearer YOUR_JWT_ACCESS_TOKEN
Content-Type: application/json
```

**Response (200 OK):**
```json
[
  {
    "rank": 1,
    "nickname": "Ali Abdullayev",
    "xp_this_week": 850,
    "is_current_user": false
  },
  {
    "rank": 2,
    "nickname": "Fotima Karimova",
    "xp_this_week": 720,
    "is_current_user": false
  },
  {
    "rank": 3,
    "nickname": "Shohjon Eshboyev",
    "xp_this_week": 680,
    "is_current_user": true
  },
  {
    "rank": 4,
    "nickname": "Zafar Rakhimov",
    "xp_this_week": 650,
    "is_current_user": false
  },
  {
    "rank": 5,
    "nickname": "Gulnora Xidirov",
    "xp_this_week": 580,
    "is_current_user": false
  }
]
```

**Ma'lumotlar Tushuntirishi:**

| Field | Nima | Misol |
|-------|------|-------|
| `rank` | Reyting o'rni | 1 = 1-o'rin, 2 = 2-o'rin |
| `nickname` | Foydalanuvchi ismi | "Ali Abdullayev" |
| `xp_this_week` | Bu hafta olingan XP | 850 |
| `is_current_user` | Hozirgi foydalanuvchimi? | `true` = Bugungi user |

**Frontend'da ishlatish:**
```javascript
// "Leaderboard" sahifasida:
//
// TOP 50 Bu Hafta:
// 🥇 1. Ali Abdullayev - 850 XP
// 🥈 2. Fotima Karimova - 720 XP
// 🥉 3. Shohjon Eshboyev - 680 XP ← YOUR (Highlight qiling!)
//    4. Zafar Rakhimov - 650 XP
//    5. Gulnora Xidirov - 580 XP
//
// is_current_user == true bo'lsa:
// - Highlight: Yellow/Gold rang
// - Icon: ⭐ yoki ✨
// - Ro'yxatni scroll qilganida to'ltirish
```

**Cache:** ✅ Cache 15 minut (uzun cache, leaderboard ko'p o'zgarmasligi uchun)

**Top 50 ta ko'rsatiladi maksimal**

---

## 📱 FRONTEND FLOW (Ketma-ketlik)

### **Scenario 1: Talaba App'ni Ochdi**

```
1. GET /progress/reviews/today/
   ↓ Response: 8 ta savol bugun takrorlash kerak
   ↓ UI: "Bugun 8 ta savol bor! 🎯"

2. GET /progress/streak/
   ↓ Response: current_streak = 45, freezes = 1
   ↓ UI: "🔥 45 kun | 🧊 1 muz"

3. GET /progress/xp/summary/
   ↓ Response: xp_today = 125, xp_this_week = 680
   ↓ UI: "📈 +125 bugun | +680 hafta"

4. GET /progress/leaderboard/weekly/
   ↓ Response: Top 50 users
   ↓ UI: "#3 position in leaderboard 🏆"
```

### **Scenario 2: Talaba Quiz'da Javob Berdi**

```
1. Quiz page'da savol ko'rsatildi
   - Timer boshlanadi (0-dan boshlanadi)
   
2. Talaba javob tanladi
   - Timer: 45 sekund o'tdi
   
3. "Check Answer" tugmasini bosdi
   - Frontend: Javobni tekshir (DB'dan savolni olish)
   - Tekshirish: is_correct = true/false
   
4. POST /progress/reviews/{id}/submit/
   - Request: { is_correct: true, response_time: 45 }
   - Response: Yangi stability_days va next_review_date
   
5. UI'da ko'rsatiladi:
   "✅ TO'G'RI! 🎉
    +50 XP olding
    Keyingi takrorlash: 11-AUGUST"
   
6. AUTO CACHE YANGILASH:
   - /reviews/today/ cache deleted
   - Keyingi o'qish tezroq bo'ladi
```

### **Scenario 3: Talaba Freeze Ishlatdi**

```
1. Streak page'da muz tugmasi ko'rsatilgan
   - freezes_available = 1
   
2. "🧊 FREEZE ISHLATISH" tugmasini bosdi
   
3. Modal: "Streaking uzilib ketmaydi. Davom etasizmi?"
   
4. "HA" tugmasini bosdi
   - POST /progress/streak/freeze/ (empty body)
   - Response: freezes_available = 0
   
5. UI'da ko'rsatiladi:
   "✅ Muz ishlatildi! 
    🔥 45 kun streak saqlanadi
    ❄️ Keyingi muz: DUSHANBA"
```

---

## 🎨 NIMALARI FRONTEND'DA KO'RSATILISH KERAK

### **Dashboard/Home Page:**
```
┌─────────────────────────────┐
│  🎯 BUGUN 8 TA SAVOL VAR    │
├─────────────────────────────┤
│  🔥 STREAK: 45 kun          │
│  🏆 BEST: 120 kun           │
│  ❄️ FREEZE: 1 mavjud        │
├─────────────────────────────┤
│  💎 XP STATISTIKA:          │
│  ✨ Jami: 2450 XP           │
│  🌟 Bugun: +125 XP          │
│  📈 Bu hafta: +680 XP       │
├─────────────────────────────┤
│  🏅 REYTING: #3 o'rin       │
│  🥉 680 XP bu haftada       │
├─────────────────────────────┤
│  ┌─ START REVIEW ───────────┤
│  │  START TEST ──────────────┤
│  │  VIEW HISTORY ────────────┤
└─────────────────────────────┘
```

### **ReviewCard List Page:**
```
┌─────────────────────────────────────┐
│  REVIEWS (TAKRORLASH KARTALAR)      │
├─────────────────────────────────────┤
│  ☐ 1. O'smanli imperiyasi           │
│     Tarix / Ortaasrlar               │
│     📅 12-AUGUST | ⭐⭐⭐ (3.5)      │
│                                      │
│  ☐ 2. Genessa shartnomasi           │
│     Tarix / Zamonaviy tarix          │
│     📅 10-AUGUST | ⭐ (1.0)          │
│                                      │
│  Filter 🔍 | Sort 📊                 │
│  ← PREV | Page 1/5 | NEXT →         │
└─────────────────────────────────────┘
```

### **Quiz Page (ReviewCard Javob):**
```
┌──────────────────────────────────────┐
│  Tarix / Ortaasrlar                  │
├──────────────────────────────────────┤
│  ⏱️ 00:45                            │
│                                      │
│  O'smanli imperiyasi qachon tuzildi? │
│                                      │
│  ○ 1300-yil                          │
│  ○ 1453-yil                          │
│  ○ 1520-yil                          │
│  ○ 1683-yil                          │
│                                      │
│  [  CHECK ANSWER  ]                  │
│  [  SKIP QUESTION ]                  │
└──────────────────────────────────────┘
```

### **Leaderboard Page:**
```
┌────────────────────────────────────┐
│  🏆 HAFTALIK LEADERBOARD           │
├────────────────────────────────────┤
│  🥇 1. Ali Abdullayev       850 XP  │
│  🥈 2. Fotima Karimova      720 XP  │
│  🥉 3. Shohjon Eshboyev  → 680 XP  │ ← YOU
│     4. Zafar Rakhimov       650 XP  │
│     5. Gulnora Xidirov      580 XP  │
│     6. Akbar Shodiev        560 XP  │
│     ...                              │
│     50. (Last in top 50)    210 XP  │
│                                     │
│  [Scroll to see more]               │
└────────────────────────────────────┘
```

### **Streak Page:**
```
┌────────────────────────────────────┐
│  🔥 KETMA-KETLIK                   │
├────────────────────────────────────┤
│  Joriy: 45 KUN ✨                  │
│  Eng uzun: 120 KUN 🏆              │
│  Oxirgi faollik: BUGUN 📅          │
│                                    │
│  ❄️ FREEZE ISHLATISH               │
│     (1 ta mavjud, haftaliga 1)     │
│                                    │
│  Eger muz ishlatmasang:             │
│  Bugun test/review qilmasang →     │
│  Streak 0 ga o'tadi! ⚠️             │
│                                    │
│  💡 TIP: Muz ishlatib o'qishni     │
│      davom ettiring! 🎯            │
└────────────────────────────────────┘
```

---

## ⚙️ API CHAQIRISH JARAYONI

### **Authentication:**
```
Barcha API'lar JWT Token talab qiladi:

1. Login/Register (Account App)
   → JWT Access Token olinadi
   
2. Har API'ga header qo'shiladi:
   Authorization: Bearer {access_token}
   
3. Token muddati tugasa:
   → Refresh Token orqali yangilash
```

### **Error Handling:**

**401 - Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```
👉 Token kerak

**403 - Forbidden:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```
👉 Roli/permissioni yo'q

**404 - Not Found:**
```json
{
  "detail": "Not found."
}
```
👉 ID topilmadi

**400 - Bad Request:**
```json
{
  "is_correct": ["This field is required."]
}
```
👉 Request formatı xato

**500 - Server Error:**
```json
{
  "detail": "Internal server error"
}
```
👉 Backend muammosi

---

## 📊 ASOSIY RAQAMLAR VA QOIDALAR

### **ReviewCard Qoidalari:**
- `stability_days`: 1.0 dan boshlanadi
- To'g'ri javob: `* 2.0` (oshadi)
- Noto'g'ri javob: `* 0.5` (kamayadi)
- Minimum: 1.0 (gapalari qayta sodir bo'lmaslik uchun)

### **Streak Qoidalari:**
- Har kun +1 (test/review qilsa)
- Uchrakmasa: 0 ga o'tadi
- Muz: 1 ta/hafta, streakni saqlab qoladi
- `freezes_available`: Dushanba ⏰ qayta yangilandi

### **XP Miqdorlari:**
- Review to'g'ri: +50 XP
- Review noto'g'ri: -10 XP
- Test yakunlash: +50-100 XP
- Streak: +5 XP/kun
- Bonus: Admin'dan

### **Cache TTL (Time-to-Live):**
- Reviews/today: 5 minut
- Streak: 5 minut
- XP Summary: 5 minut
- Leaderboard: 15 minut
- Transactions: Cache yo'q (har safar fresh)

### **Limit & Pagination:**
- Barcha list API'lari: 20-30 ta/sahifa
- Leaderboard: Max 50 ta entry

---

## 🎯 FRONTEND CHECKLIST

- [ ] Dashboard'da barcha 4 ta widget ko'rsatiladi
- [ ] "Bugun X ta savol" countdown o'zlashtirilgan
- [ ] ReviewCard list'da filterlash ishlaydi
- [ ] Quiz page'da timer ishlaydi (sekund cinsida)
- [ ] Quiz'da javob tekshirish ishlaydi
- [ ] POST /reviews/submit/ chaqiriladi
- [ ] Success/Error message ko'rsatiladi
- [ ] Streak page'da "Muz" tugmasi aktiv/inactive
- [ ] Freeze modal confirmation ishlaydi
- [ ] Leaderboard'da current user highlight qilingan
- [ ] Pagination barcha listlarda ishlaydi
- [ ] Authorization header har API'ga qo'shiladi
- [ ] Error handling qilingan
- [ ] Cache'dan foydalanish (LD'dan o'qish tezroq)
- [ ] Loading spinners ko'rsatiladi

---

## 💬 FRONTEND SAVOLLARI VA JAVOBLARI

### **S: Muz nima va qachon ishlatiladi?**
**J:** Muz - Streak (ketma-ketlik) uzilib ketmaydi deb o'tkazib ketilgan kun. Haftaliga 1 marta ishlatish mumkin. Bugun test/review qilmasang ham streak +1 qo'shilib qoladi.

### **S: Stability_days nima?**
**J:** Savolni takrorish vaqti (kunlarda). To'g'ri javob bersa oshadi (1.0 → 2.0 → 4.0...), noto'g'ri bo'lsa kamayadi (3.0 → 1.5 → 0.75...). Minimum 1.0 kun.

### **S: Response_time nima?**
**J:** Savolga javob berish uchun sarflangan vaqt (soniyalarda). Misol: 45 = 45 sekund. Frontend'da timer'dan olinadi.

### **S: XP qanday o'zgaradi?**
**J:** Test/review qilganida XPTransaction yaratiladi (+50, -10, +100, etc.). XP Total'ga qo'shilib qoladi. Leaderboard haftalik XP bo'yicha hisoblanadi.

### **S: Nima uchun POST /reviews/submit/ ga body kerak, lekin POST /streak/freeze/ ga body kerak emas?**
**J:** Submit'da `is_correct` va `response_time` kerak (tayin javob). Freeze'da foydalanuvchi ma'lum (request.user'dan) va amal bir xil (muz ishlatish) shuning uchun body kerak emas.

### **S: Cache nima uchun kerak?**
**J:** API'ni har safar chaqirmay, previously saved data'ni qaytarish. Tezroq yuklash, server bemorasi kamayadi. Misol: /reviews/today/ 5 minut cache'da qoladi, 5 minut o'tgani bilan yangilandi.

### **S: Leaderboard Top 50'da qatnashmasam nima?**
**J:** Response'da qatnashmaysiz. Faqat Top 50'da ko'rsatiladi. Agar bu haftada ko'proq XP olsangiz, top 50'ga kirasiz.

### **S: Streak 0 bo'ldi, qayta boshlasam?**
**J:** Ha, bugungi test/review qilsang `current_streak = 1` dan boshlanadi. Qayta 45 kun'ni topshing 😅

### **S: Necha marta freeze ishlatish mumkin?**
**J:** Haftaliga 1 marta. Dushanba ⏰ qayta yangilandi (freezes_available = 1).

### **S: ReviewCard avtomatik yaratilasmi?**
**J:** Ha! Test qilganida testengine app'dan chaqiriladi. O'qituvchi sau'ol qo'shganida, "Barcha foydalanuvchilarga ReviewCard" yaratiladi.

### **S: DELETE API nima uchun yo'q?**
**J:** Audit trail (tarix) uchun. XP, ReviewCard, Streak'ni o'chirish kerak emas - statistika hisoblanadi. Faqat softly delete bo'lishi mumkin (eski data saqlanadi).

### **S: PATCH API nima uchun yo'q?**
**J:** Server har harakatdan keyin stabilitini o'zi hisoblab qiladi. Frontend'dan qo'l bilan o'zgartirish kerak emas. POST (harakat) → Server o'zgartirir.

---

## 🔧 INTEGRATION TIPS

### **Frontend'dan API Chaqirish (JavaScript/Axios):**

```javascript
// 1. Token oling (Login'dan)
const token = localStorage.getItem('access_token');

// 2. Headers qo'shiladi
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};

// 3. GET - Barcha kartalar
axios.get('http://localhost:8000/progress/reviews/', { 
  headers,
  params: { page: 1 }
})
.then(res => console.log(res.data))
.catch(err => console.log(err.response.data));

// 4. GET - Bugun takrorlash
axios.get('http://localhost:8000/progress/reviews/today/', { headers })
.then(res => console.log(res.data));

// 5. POST - Javob berish
axios.post('http://localhost:8000/progress/reviews/2/submit/', 
  { is_correct: true, response_time: 45 },
  { headers }
)
.then(res => console.log(res.data));

// 6. GET - Streak
axios.get('http://localhost:8000/progress/streak/', { headers });

// 7. POST - Freeze
axios.post('http://localhost:8000/progress/streak/freeze/', 
  {},
  { headers }
);

// 8. GET - XP Summary
axios.get('http://localhost:8000/progress/xp/summary/', { headers });

// 9. GET - Leaderboard
axios.get('http://localhost:8000/progress/leaderboard/weekly/', { headers });
```

---

## 📞 SUPPORT

Agar API'da muammo bo'lsa:
1. `response.status` va `response.data` ko'rish
2. Token amalmi tekshirish
3. Backend logs ko'rish
4. Postman'da test qilish

---

**Oxirgi yangilash:** 2026-08-09
**Version:** 1.0
