# Yangi va o'zgargan API'lar — frontend uchun

> Bu hujjat faqat **oxirgi ishda qo'shilgan** endpointlar haqida.
> Eski endpointlar [Frontend_API.md](Frontend_API.md) da tursa, o'sha kuchda qoladi.
>
> **Jami: 13 ta yangi yo'l, 17 ta operatsiya** + 8 ta javob shakli o'zgargan endpoint.

| Belgi | Ma'nosi |
|---|---|
| 🔓 | Token kerak emas |
| 🔑 | `Authorization: Bearer <access_token>` kerak |
| 👑 | Faqat `role = admin` |

Barcha xato javoblarida `detail` (odamga ko'rsatiladigan matn) va ko'pincha
`code` (dasturiy kalit) keladi. Tarif yetmagan joyda qo'shimcha
`upgrade_required: true` — shu belgini ko'rsangiz, foydalanuvchini tariflar
sahifasiga olib boring.

---

## 1. Kirish testi (Intro) — ro'yxatdan o'tishdan oldin

Ilovani birinchi marta ochgan odamga ko'rsatiladigan qisqa test: **tasodifiy
4 ta** mantiqiy yoki psixologik savol. Maqsadi — qiziqtirib, ro'yxatdan
o'tkazish. Ro'yxatdan o'tgan foydalanuvchiga ko'rsatilmaydi.

### 🔓 `GET /intro/start/`
Testni boshlaydi: 4 ta tasodifiy savol va `token` qaytaradi.

**Javob:**
```json
{
  "token": "imzolangan-token",
  "question_count": 4,
  "questions": [
    {
      "id": 12,
      "kind": "logic",
      "text": "Qatordagi keyingi son nechchi?",
      "options": {"A": "8", "B": "9", "C": "10"},
      "image": "https://.../media/intro/images/2026/09/savol.png",
      "video": null,
      "video_url": "https://youtu.be/xxxx"
    }
  ]
}
```

- `kind`: `logic` (to'g'ri javobi bor) yoki `psychology` (to'g'ri javob yo'q).
- `image`, `video` — to'liq URL yoki `null`. `video_url` — tashqi havola (YouTube).
- **To'g'ri javob javobda yo'q** — u faqat `submit` dan keyin keladi.
- `token` 1 soat amal qiladi, uni `submit` ga qaytarib yuborasiz.

**Xatolar:** `403 already_registered` (foydalanuvchi tizimga kirgan),
`503 not_enough_questions` (bazada 4 ta faol savol yo'q).

### 🔓 `POST /intro/submit/`
Javoblarni yuboradi va natijani qaytaradi.

**So'rov:**
```json
{
  "token": "start dan olingan token",
  "answers": [
    {"question": 12, "selected_option": "B"},
    {"question": 15, "selected_option": "A"}
  ]
}
```

**Javob:**
```json
{
  "question_count": 4,
  "answered_count": 2,
  "correct_count": 1,
  "scored_count": 3,
  "results": [
    {"question": 12, "kind": "logic", "selected_option": "B",
     "correct_option": "B", "is_correct": true, "explanation": "Chunki..."}
  ],
  "message": "Yaxshi boshladingiz! Ro'yxatdan o'tsangiz...",
  "registration_required": true
}
```

- `scored_count` — baholanadigan (mantiqiy) savollar soni. Psixologik savolda
  `is_correct: null` keladi — uni "xato" deb ko'rsatmang.
- Tokendagi ro'yxatda yo'q savolga berilgan javob e'tiborga olinmaydi.

**Xatolar:** `400 invalid_token`, `400 token_expired`, `403 already_registered`.

### 👑 Kirish testi savollarini boshqarish

| Metod | Yo'l | Vazifasi |
|---|---|---|
| GET | `/intro/admin/questions/` | Ro'yxat. Filtrlar: `?kind=logic|psychology`, `?is_active=true` |
| POST | `/intro/admin/questions/` | Yangi savol qo'shish |
| GET | `/intro/admin/questions/<id>/` | Bitta savol |
| PATCH | `/intro/admin/questions/<id>/` | Tahrirlash |
| DELETE | `/intro/admin/questions/<id>/` | O'chirish |

**Rasm va video yuklash:** `multipart/form-data` bilan yuboriladi
(`image`, `video` maydonlari). Matn bilan ishlasangiz `application/json` ham
qabul qilinadi.

**Maydonlar:** `kind`, `text` / `text_ru` / `text_en`, `options` /
`options_ru` / `options_en`, `correct_option`, `image`, `video`, `video_url`,
`explanation` / `explanation_ru` / `explanation_en`, `order`, `is_active`.

**Qoidalar (400 qaytaradi):**
- `options` da kamida 2 ta variant bo'lishi kerak;
- `kind=logic` bo'lsa `correct_option` majburiy va u variantlar ichida bo'lishi shart;
- `kind=psychology` bo'lsa `correct_option` bo'sh bo'lishi kerak;
- video hajmi 50 MB dan oshmasligi kerak (kattasi uchun `video_url` ishlating).

---

## 2. Foydalanuvchilarni boshqarish (admin) 👑

### `GET /dashboard/admin/users/`
Foydalanuvchilar ro'yxati + tepadagi umumiy raqamlar.

**Query parametrlar:**

| Parametr | Vazifasi |
|---|---|
| `search` | Email, ism, telefon yoki Telegram username bo'yicha qidirish |
| `role` | `student` / `mentor` / `admin` / `support` |
| `is_active` | `false` — faqat bloklanganlar |
| `tier` | `pro` — faol pullik obunasi borlar, `free` — qolganlar |
| `ordering` | `-created_at` (standart), `created_at`, `-xp_total`, `-last_login`, `email` |
| `page`, `page_size` | Sahifalash |

**Javob:** odatdagi sahifalangan ro'yxat + `stats` obyekti:
```json
{
  "count": 120, "next": "...", "previous": null,
  "results": [
    {"id": 13, "email": "ali@gmail.com", "full_name": "Ali Valiyev",
     "role": "student", "avatar_url": "", "xp_total": 430,
     "is_active": true, "is_blocked": false, "blocked_at": null,
     "blocked_by_email": null, "block_reason": "",
     "last_login": "2026-09-20T10:11:00Z", "created_at": "2026-08-01T08:00:00Z"}
  ],
  "stats": {"total": 120, "blocked": 3, "students": 115, "mentors": 2, "pro": 18}
}
```

### `GET /dashboard/admin/users/<id>/`
Bitta foydalanuvchi kartasi. Ro'yxatdagi maydonlarga qo'shimcha:

- `phone_number`, `telegram_username`, `region`, `target_major`, `language`
- `subscription`: `{plan, plan_id, expires_at, days_left}` yoki `null`
- `entitlements`: tarifi bo'yicha barcha limitlari (quyida 5-bo'limga qarang)
- `sessions_total`, `sessions_finished`, `last_test_at`, `devices_count`

### `POST /dashboard/admin/users/<id>/block/`
Foydalanuvchini bloklaydi. Tanasi ixtiyoriy: `{"reason": "Qoidabuzarlik"}`.

Bloklangan odam **API'ga umuman kira olmaydi** — tokeni qo'lida bo'lsa ham
401 oladi. Javobda yangilangan foydalanuvchi qatori qaytadi
(`is_blocked: true`, `blocked_by_email`, `block_reason`).

**Xatolar:** `400 self_block` (o'zini bloklash), `400 admin_block`
(administratorni bloklash), `404` (topilmadi).

### `POST /dashboard/admin/users/<id>/unblock/`
Blokni ochadi, sabab va vaqt tozalanadi.

---

## 3. DTM blok imtihoni (Mock exam) 🔑

Bir nechta fan ketma-ket, **bitta umumiy taymer** bilan. Tarifda
`mock_exam` ptichkasi bo'lishi kerak, aks holda `403`.

### `POST /testengine/mock-exams/`
```json
{"subjects": [1, 2, 3], "question_count": 30}
```
- 2 tadan 5 tagacha fan; `question_count` — HAR BIR fandagi savol soni
  (20, 25, ... 60 dan biri).
- Har bir fan uchun alohida `TestSession` ochiladi; javob berish uchun
  **mavjud** `/testengine/sessions/<id>/...` endpointlari ishlatiladi.

**Javob (201):**
```json
{
  "id": 7, "time_limit_seconds": 5400,
  "expires_at": "2026-09-23T12:00:00Z", "seconds_left": 5400,
  "finished_at": null, "is_finished": false, "auto_finished": false,
  "subjects": [
    {"session_id": 41, "order": 1, "subject": {"id": 1, "name": "Matematika"},
     "question_count": 30, "is_finished": false,
     "correct_count": 0, "incorrect_count": 0, "unanswered_count": 0, "total_score": 0}
  ],
  "summary": {"total_questions": 90, "correct_count": 0, "incorrect_count": 0,
              "unanswered_count": 0, "total_score": 0, "accuracy_percent": 0.0}
}
```

**Xatolar:** `403` (tarifda yo'q), `400 exam_already_open` (tugallanmagan
imtihon bor, `exam_id` ham keladi), `400 not_enough_questions`,
`400 question_count_exceeded`.

### `GET /testengine/mock-exams/<id>/`
Imtihon holati va qolgan vaqt (`seconds_left`). Muddat o'tgan bo'lsa shu
so'rovning o'zida avtomatik yakunlanadi (`auto_finished: true`).

### `POST /testengine/mock-exams/<id>/finish/`
Imtihonni yakunlaydi: ochiq qolgan fanlar ham yopiladi, `summary` to'ladi.

### `GET /testengine/mock-exams/`
Foydalanuvchining imtihonlari (sahifalangan). Tarifdagi «Natijalar tarixi»
chegarasi bu yerda ham amal qiladi.

---

## 4. Natijalarni yuklab olish 🔑

### `GET /testengine/results/export/?type=xlsx`
Natijalar tarixini fayl qilib beradi. `type`: `xlsx` (standart) yoki `pdf`.

> Parametr nomi ataylab `format` emas — `format` ni DRF o'zi ishlatadi.

Javob — faylning o'zi (`Content-Disposition: attachment`). Frontendda
`responseType: 'blob'` bilan oling. Tarifda `export_results` ptichkasi
bo'lmasa `403`. Bir faylda ko'pi bilan 5000 qator.

---

## 5. Tariflar: ptichkalar va limitlar

### 👑 `GET /billing/plan/features/`
Admin panelda tarif yaratish formasini **shu javobdan chizing**. Kodda
birorta tarif nomi yozilmagan: admin xohlagancha bosqich yaratadi (Basic,
Pro, Premium, Premium Max...) va ptichkalarni o'zi belgilaydi.

```json
{
  "groups": [{"key": "test", "label": "Test ishlash"}, ...],
  "features": [
    {"key": "daily_topic_limit", "storage": "field", "kind": "limit",
     "group": "test", "enforced": true, "label": "Kunlik mavzu limiti",
     "help": "...", "unlimited_when_empty": true},
    {"key": "max_question_count", "kind": "choice", "choices": [20, 25, 30, ...]},
    {"key": "mock_exam", "storage": "feature", "kind": "flag", "enforced": true}
  ]
}
```

| Maydon | Ma'nosi |
|---|---|
| `kind` | `flag` → ptichka, `limit` → raqam maydoni, `choice` → ro'yxatdan tanlash |
| `storage` | `field` → tarifning o'z maydoni, `feature` → `features` JSON ichidagi kalit |
| `unlimited_when_empty` | Raqam bo'sh qoldirilsa **cheksiz** degani (`0` → imkoniyat yopiq) |
| `enforced` | `false` bo'lsa backend hali tekshirmaydi (hozir faqat `ai_tutor` shunday) |

### ⚠️ `POST /billing/plan/` va `PATCH /billing/plan/<id>/` 👑
Endi nom va narxdan tashqari **barcha cheklovlar** ham qabul qilinadi:
`daily_topic_limit`, `max_question_count`, `can_choose_question_count`,
`can_use_exam_mode`, `can_view_explanations`, `explanation_limit_per_day`,
`mistake_test_daily_limit`, `review_cards_daily_limit`, `can_view_analytics`,
`history_days`, `streak_freezes_per_month`, `features` (JSON).

`features` ichidagi kalitlar: `mock_exam`, `export_results`,
`mentor_support`, `priority_support`, `ai_tutor`.

**Qoida:** raqam bo'sh (`null`) → cheksiz, `0` → yopiq.
`is_pro` faqat belgi — u hech qanday limitni bekor qilmaydi.

### ⚠️ `GET /billing/plan/` va `GET /billing/plan/<id>/`
Endi shu maydonlarning hammasini qaytaradi — tarif kartasida «nima kiradi»
ro'yxatini shundan chizing.

---

## 6. O'zgargan javob shakllari

| Endpoint | Nima o'zgardi |
|---|---|
| `GET /progress/reviews/today/` | `due_total`, `limit`, `used_today`, `remaining_today`, `upgrade_required` qo'shildi. `results` endi kunlik limitdan qolganicha qirqiladi, `count` esa ko'rsatilgan kartalar soni |
| `POST /progress/reviews/<id>/submit/` | Kunlik limit tugasa `403 review_card_limit_reached` |
| `GET /progress/streak/` | `freezes_limit_per_month`, `freezes_used_this_month`, `freezes_remaining` qo'shildi (`null` → cheksiz) |
| `POST /progress/streak/freeze/` | Oylik limit: tugasa `403 streak_freeze_limit_reached`, tarifda yo'q bo'lsa `403 upgrade_required` |
| `POST /testengine/mistakes/start-test/` | Kunlik limit: `403 mistake_test_limit_reached` yoki `403 upgrade_required` |
| `POST /testengine/sessions/` va `.../start-test/` | `mode=exam` tarifda yopiq bo'lsa `403 exam_mode_unavailable` |
| `GET /billing/payments/info/` | `priority_support: true/false` qo'shildi, matn ham shunga qarab o'zgaradi |
| `POST /dashboard/mentor/students/` | Ishlaydigan bo'ldi (avval 500 qaytarardi). Talabaning tarifida `mentor_support` bo'lmasa `403 upgrade_required` |

Yana: `/rating/weak-topics/`, `/rating/topics/`, `/rating/subjects/`,
`/rating/history/` endi tarifda `can_view_analytics` yo'q bo'lsa `403`
qaytaradi. `/rating/me/`, leaderboard va liga hammaga ochiq qoladi.

---

## 7. Yangi xato kodlari

| Kod | Qachon |
|---|---|
| `already_registered` | Kirish testini ro'yxatdan o'tgan odam so'radi |
| `invalid_token`, `token_expired` | Kirish testi tokeni yaroqsiz yoki eskirgan |
| `not_enough_questions` | Kirish testida yoki blok imtihonida savol yetmadi |
| `exam_already_open` | Tugallanmagan blok imtihoni bor |
| `exam_mode_unavailable` | Imtihon rejimi tarifda yopiq |
| `mistake_test_limit_reached` | Xatolardan test tuzish kunlik limiti tugadi |
| `review_card_limit_reached` | Takrorlash kartalari kunlik limiti tugadi |
| `streak_freeze_limit_reached` | «Muz» oylik limiti tugadi |
| `question_count_exceeded` | Tarifdagi maksimal savoldan ko'p so'raldi |
| `unsupported_format` | Eksportda `type` noto'g'ri |
| `self_block`, `admin_block` | Adminni yoki o'zini bloklashga urinish |
| `upgrade_required` | Imkoniyat tarifda umuman yo'q |
