# TestYourself — Frontend uchun to'liq API ro'yxati

> DTM test platformasining **barcha** endpointlari: qaysi biri nima vazifa bajaradi,
> so'rovda nima yuboriladi, javobda nima keladi.
> Kod yo'q — faqat tushuntirish.

**Jami: 86 ta yo'l, 121 ta operatsiya.**

| Belgi | Ma'nosi |
|---|---|
| 🆕 | Yangi qo'shilgan endpoint |
| ⚠️ | Eskidan bor, lekin javob shakli yoki so'rov talabi **o'zgargan** |
| 🔓 | Token kerak emas |

---

## MUNDARIJA

| № | Bo'lim | Yo'l | Operatsiya |
|---|---|---|---|
| 1 | [Umumiy qoidalar](#1-umumiy-qoidalar) | — | — |
| 2 | [Foydalanuvchi oqimi](#2-foydalanuvchi-oqimi) | — | — |
| 3 | [Autentifikatsiya](#3-autentifikatsiya--api) | 7 | 9 |
| 4 | [Katalog](#4-katalog--catalog) | 8 | 24 |
| 5 | [Test dvijoki](#5-test-dvijoki--testengine) | 24 | 33 |
| 6 | [Progress](#6-progress--progress) | 9 | 9 |
| 7 | [Reyting](#7-reyting--rating) | 11 | 11 |
| 8 | [Obuna va to'lov](#8-obuna-va-tolov--billing) | 12 | 17 |
| 9 | [Bildirishnomalar](#9-bildirishnomalar--notifications) | 5 | 6 |
| 10 | [Dashboard](#10-dashboard--dashboard) | 10 | 12 |
| 11 | [Xato kodlari](#11-xato-kodlari) | — | — |
| 12 | [Ekran → so'rov xaritasi](#12-ekran--sorov-xaritasi) | — | — |

---

## 1. UMUMIY QOIDALAR

### Autentifikatsiya
Barcha so'rovlarda header: `Authorization: Bearer <access_token>`

**Istisno (token kerak emas):**
`/api/auth/google/` · `/api/auth/apple/` · `/api/auth/refresh/` · `/testengine/guest/topics/` · `/testengine/guest/start/` · `/testengine/guest/submit/`

`access` token 1 soat, `refresh` token 30 kun amal qiladi.

### Til
Uchta usul (yuqoridagisi ustun):
1. `?lang=uz` yoki `?lang=ru` yoki `?lang=en`
2. `X-Language: ru` header
3. Foydalanuvchi profilidagi til, keyin `Accept-Language`

Tarjima kiritilmagan bo'lsa o'zbekchasi qaytadi — bo'sh matn hech qachon chiqmaydi.

### Sahifalash
`?page=1&page_size=20` — maksimum `page_size` 100.
Javob shakli: `count`, `next`, `previous`, `results`.

### Vaqt
Barcha sanalar **Toshkent vaqtida** (`+05:00`). Kun mahalliy yarim tunda almashadi.

### Xato shakli
Har bir xatoda `detail` (o'zbekcha tayyor matn) va ko'pincha `code` bo'ladi.
Matnni front o'zi yozmaydi — `detail` ni to'g'ridan-to'g'ri ekranga chiqarsa bo'ladi.

### Rollar va darajalar
**Rollar:** `student` · `mentor` · `admin` · `support`
**Obuna darajalari:** `guest` (ro'yxatdan o'tmagan) · `free` · `pro` (Pro-Basic va Pro-Full)

### Hujjatlar
`/swagger/` · `/redoc/` · `/schema/` — prodda faqat admin uchun ochiq.

---

## 2. FOYDALANUVCHI OQIMI

Test boshlashgacha bo'lgan yo'l — bu haqiqiy ketma-ketlik, har bir qadam oldingisining javobiga tayanadi:

| № | Qadam | So'rov |
|---|---|---|
| 1 | Fan tanlash | `GET /catalog/subjects/` |
| 2 | **Sinf/kitob tanlash** 🆕 | `GET /catalog/grades/?subject={id}` |
| 3 | Mavzu tanlash | `GET /catalog/topics/?grade={id}&has_test=true` |
| 4 | **Savol soni tanlash** 🆕 | `GET /testengine/topics/{id}/available-counts/` |
| 5 | Testni boshlash 🆕 | `POST /testengine/topics/{id}/start-test/` |
| 6 | Test varaqasi | `GET /testengine/sessions/{id}/questions/` |
| 7 | Javob berish / o'zgartirish | `POST /testengine/sessions/{id}/questions/{order}/answer/` |
| 8 | Yakunlash | `POST /testengine/sessions/{id}/finish/` |
| 9 | Tahlil | `GET /testengine/sessions/{id}/review/` |

**Kontent ierarxiyasi:** Fan → Sinf/Kitob → Mavzu → Savol

---

## 3. AUTENTIFIKATSIYA — `/api/`

**7 ta yo'l · 9 ta operatsiya**

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `POST` | `/api/auth/google/` 🔓 | Google hisobi orqali kirish. `id_token` yuboriladi, javobda `access` + `refresh` token va foydalanuvchi ma'lumoti keladi. Hisob yo'q bo'lsa avtomatik yaratiladi |
| `POST` | `/api/auth/apple/` 🔓 | Apple ID orqali kirish. Google bilan bir xil ishlaydi |
| `POST` | `/api/auth/refresh/` 🔓 | `access` token muddati tugaganda uni `refresh` token bilan yangilaydi |
| `POST` | `/api/auth/logout/` | Chiqish. `refresh` token bekor qilinadi (qora ro'yxatga tushadi) |
| `GET` | `/api/auth/me/` | Mening profilim: ism, email, avatar, rol, til, telefon, region, yo'nalish, umumiy XP, obuna holati |
| `PATCH` | `/api/auth/me/` | Profilni tahrirlash: `full_name`, `language`, `phone_number`, `telegram_username`, `region`, `target_major`, `consent_share_with_universities`. **`role` va `xp_total` ni o'zgartirib bo'lmaydi** |
| `GET` | `/api/auth/devices/` | Mening qurilmalarim ro'yxati |
| `POST` | `/api/auth/devices/` | Qurilmani ro'yxatdan o'tkazish. `device_id`, `platform` (`ios`/`android`/`web`/`desktop`), `push_token`, `model_name`, `os_version`, `app_version`. Bir qurilma bir marta yoziladi — takror yuborilsa yangilanadi |
| `DELETE` | `/api/auth/devices/{device_id}/` | Qurilmani o'chirish (push bildirishnoma to'xtaydi) |

---

## 4. KATALOG — `/catalog/`

**8 ta yo'l · 24 ta operatsiya**

### 4.1. Fanlar

| Metod | Yo'l | Vazifasi | Kim |
|---|---|---|---|
| `GET` ⚠️ | `/catalog/subjects/` | Fanlar ro'yxati | Hamma |
| `POST` | `/catalog/subjects/` | Yangi fan yaratish | Mentor · Admin |
| `GET` | `/catalog/subjects/{id}/` | Bitta fan haqida ma'lumot | Hamma |
| `PUT` `PATCH` | `/catalog/subjects/{id}/` | Fan nomini va tarjimalarini tahrirlash | Mentor · Admin |
| `DELETE` | `/catalog/subjects/{id}/` | Fanni o'chirish. Ichida mavzu bo'lsa **409** qaytadi | Mentor · Admin |

**Javobda:** `id`, `name`, `translations` (uz/ru/en), `grade_count`, `topic_count`, `has_test`, `created_at`, `updated_at`

⚠️ **Yangi maydonlar:** `grade_count`, `topic_count`, `has_test`.
`has_test` — shu fanda test ochish mumkin bo'lgan mavzu bormi. Bo'sh fanni kulrang qilish yoki yashirish uchun.

**Filtr:** `?name=` — uchala tilda qidiradi.

---

### 4.2. Sinflar / Kitoblar 🆕

Fan bilan mavzu orasidagi yangi bosqich. Nom **erkin matn**: «7-sinf» ham, «Milliy sertifikat uchun» ham, «Abituriyentlar uchun» ham bo'laveradi.

| Metod | Yo'l | Vazifasi | Kim |
|---|---|---|---|
| `GET` 🆕 | `/catalog/grades/` | Fan ichidagi sinflar va kitoblar ro'yxati | Hamma |
| `POST` 🆕 | `/catalog/grades/` | Yangi sinf yoki kitob yaratish | Mentor · Admin |
| `GET` 🆕 | `/catalog/grades/{id}/` | Bitta sinf haqida ma'lumot | Hamma |
| `PUT` `PATCH` 🆕 | `/catalog/grades/{id}/` | Nomini, tartibini yoki faolligini o'zgartirish | Mentor · Admin |
| `DELETE` 🆕 | `/catalog/grades/{id}/` | O'chirish. Ichida mavzu bo'lsa **409** qaytadi | Mentor · Admin |

**Javobda:** `id`, `subject`, `subject_name`, `name`, `translations`, `order`, `is_active`, `topic_count`, `has_test`

**Yaratishda yuboriladi:** `subject` (majburiy), `name` (majburiy), `name_ru`, `name_en`, `order`, `is_active`

**Filtrlar:** `?subject=` · `?name=` · `?is_active=`

> **Muhim:** Ro'yxat alifbo bo'yicha emas, `order` bo'yicha keladi. Aks holda «10-sinf» «7-sinf» dan oldin chiqib qolardi.
> Bir fan ichida bir xil nom ikki marta bo'lolmaydi.

---

### 4.3. Mavzular

| Metod | Yo'l | Vazifasi | Kim |
|---|---|---|---|
| `GET` ⚠️ | `/catalog/topics/` | Mavzular ro'yxati | Hamma |
| `POST` ⚠️ | `/catalog/topics/` | Yangi mavzu yaratish | Mentor · Admin |
| `GET` | `/catalog/topics/{id}/` | Bitta mavzu | Hamma |
| `PUT` `PATCH` | `/catalog/topics/{id}/` | Tahrirlash | Mentor · Admin |
| `DELETE` | `/catalog/topics/{id}/` | O'chirish. Savoli bo'lsa **409** qaytadi | Mentor · Admin |

**Javobda:** `id`, `subject`, `subject_name`, `grade`, `grade_name`, `name`, `translations`, `order`, `is_active`, `has_test`, `available_counts`, `question_count`

⚠️ **O'zgardi — frontend albatta o'qisin:**
- Yaratishda endi `subject` emas, **`grade`** yuboriladi. Fan avtomatik aniqlanadi. `grade` yuborilmasa **400** qaytadi
- Yangi maydonlar: `grade`, `grade_name`, `has_test`, `available_counts`, `question_count`, `order`, `is_active`
- `available_counts` — **shu foydalanuvchi** tanlay oladigan savol sonlari (guestda faqat `[20]`)
- `question_count` — **talabaga har doim `null`**, faqat mentor va admin haqiqiy sonni ko'radi

**Filtrlar:** `?subject=` · `?grade=` · `?name=` · `?is_active=` · **`?has_test=true`** (bo'sh mavzularni ro'yxatdan chiqarib tashlaydi)

---

### 4.4. Savollar

| Metod | Yo'l | Vazifasi | Kim |
|---|---|---|---|
| `GET` | `/catalog/questions/` | Savollar ro'yxati. Talaba faqat **chop etilgan va faol** savollarni ko'radi | Hamma |
| `POST` | `/catalog/questions/` | Yangi savol yaratish. Rasm bilan `multipart/form-data`, rasmsiz oddiy JSON | Mentor · Admin |
| `GET` | `/catalog/questions/{id}/` | Bitta savol. Talabaga `correct_option` **ko'rsatilmaydi** | Hamma |
| `PUT` `PATCH` | `/catalog/questions/{id}/` | Tahrirlash. Rasmni olib tashlash uchun `image: null` | Mentor · Admin |
| `DELETE` | `/catalog/questions/{id}/` | O'chirish. Javob berilgan yoki ochiq sessiyada bo'lsa **409** | Mentor · Admin |

**Asosiy maydonlar:** `topic`, `text` (+`_ru`/`_en`), `options` (A/B/C/D ko'rinishida), `correct_option`, `difficulty` (1–5), `image`, `image_caption`

**Yechim izohi maydonlari:** `explanation` (+`_ru`/`_en`), `explanation_image`, `hint`

**Holat va manba:** `status` (`draft` · `review` · `published` · `archived`), `is_active`, `source`, `source_year`

**Statistika (avtomatik hisoblanadi):** `times_answered`, `times_correct`, `p_value` (haqiqiy yengillik), `observed_difficulty`, `avg_time_seconds`

> Testga faqat `status: published` **va** `is_active: true` savollar tushadi.
> Xato savolni o'chirmasdan muomaladan chiqarish uchun `is_active` ni `false` qilish yetarli — javoblar tarixi buzilmaydi.

**Filtrlar:** `?topic=` · `?grade=` · `?subject=` · `?difficulty=` · `?difficulty_min=` · `?difficulty_max=` · `?text=` · `?has_image=` · `?status=` · `?is_active=` · `?source=` · `?source_year=` · `?has_explanation=`

---

## 5. TEST DVIJOKI — `/testengine/`

**24 ta yo'l · 33 ta operatsiya**

### 5.1. Test boshlash 🆕

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` 🆕 | `/testengine/topics/{topic_id}/available-counts/` | **Nechta savol tanlash mumkin** + kunlik limit holati |
| `POST` 🆕 | `/testengine/topics/{topic_id}/start-test/` | **Testni boshlash** |
| `GET` 🆕 | `/testengine/my-limits/` | Bugun yana nechta mavzu qolgani |

#### `available-counts` — savol soni ekrani

Savol soni ekranining butun mazmuni shu bitta so'rovda keladi.

**Javobda:**
- `tiers` — tanlash mumkin bo'lgan sonlar ro'yxati (tugmalar shundan)
- `is_available` — test ochish mumkinmi
- `reason` — mumkin bo'lmasa tayyor o'zbekcha xabar
- `min_required` — minimal savol soni (20)
- `access` — kunlik limit holati: `can_start`, `daily_topic_limit`, `topics_used_today`, `topics_remaining_today`, `reset_at`, `upgrade_required`
- `entitlements` — foydalanuvchi darajasi va imkoniyatlari
- `topic`, `subject`, `grade` — nomlar bilan
- `question_count` — **talabaga har doim `null`**

**Bosqichlar:** `20 · 25 · 30 · 35 · 40 · 45 · 50 · 55 · 60`

> **Qoida:** mavzuda **43 ta** savol bo'lsa foydalanuvchiga faqat `20, 25, 30, 35, 40` chiqadi.
> 45 ko'rinmaydi, chunki bazada shuncha savol yo'q.
> Mavzuda 20 tadan kam savol bo'lsa ro'yxat bo'sh keladi va test umuman ochilmaydi.
>
> Foydalanuvchi mavzudagi savollar sonini **hech qachon ko'rmaydi** — u faqat tanlay oladigan variantlarni ko'radi.

#### `start-test` — testni boshlash

**Yuboriladi:** `count` (yuqoridagi `tiers` dan biri) va `mode` — `practice` (taymersiz) yoki `exam` (server tomonda taymer).
`count` berilmasa eng kichik bosqich olinadi.

**Javobda sessiya:** `id`, `question_count`, `topic`, `grade`, `subject`, `mode`, `started_at`, va imtihon rejimida `time_limit_seconds`, `expires_at`, `seconds_left`.

Savollar shu daqiqada tanlanib **qotiriladi** — test davomida ular va tartibi o'zgarmaydi.

**Xatolar:**

| HTTP | Kod | Qachon |
|---|---|---|
| 400 | `not_enough_questions` | Mavzuda 20 tadan kam savol |
| 400 | `invalid_count` | Tanlangan son bosqichlar ro'yxatida yo'q |
| **403** | **`daily_topic_limit_reached`** | **Free foydalanuvchi kunlik 4 ta mavzu limitiga yetdi** |

> 403 javobida `reset_at` bor — «ertaga 00:00 dan keyin» yozuvini shundan oling va **Pro taklifi oynasini** chiqaring.

#### `my-limits` — bosh sahifa ko'rsatkichi

Test boshlamasdan turib limitni bilish uchun.

**Javobda:** `daily_topic_limit`, `topics_used_today`, `topics_remaining_today`, `reset_at`, `question_count_tiers`, `entitlements`

> Pro foydalanuvchida `daily_topic_limit` va `topics_remaining_today` — **`null`**, ya'ni cheklov yo'q. Front bunda «Cheksiz» deb ko'rsatadi.

---

### 5.2. Test ishlash

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` ⚠️ | `/testengine/sessions/{id}/questions/` | **Butun test varaqasi** — barcha savollar bir so'rovda |
| `GET` | `/testengine/sessions/{id}/questions/{order}/` | Bitta savol (tartib raqami bo'yicha) |
| `POST` | `/testengine/sessions/{id}/questions/{order}/` | Javob berish (yuqoridagining muqobili) |
| `DELETE` | `/testengine/sessions/{id}/questions/{order}/` | Javobni o'chirish |
| `GET` | `/testengine/sessions/{id}/questions/{order}/answer/` | Bitta savol va mening javobim |
| `POST` | `/testengine/sessions/{id}/questions/{order}/answer/` | **Javob berish yoki O'ZGARTIRISH** |
| `DELETE` | `/testengine/sessions/{id}/questions/{order}/answer/` | **Tanlovni bekor qilish** |
| `GET` ⚠️ | `/testengine/sessions/{id}/progress/` | Nechta javoblangan, qaysilari bo'sh, **qancha vaqt qolgan** |
| `GET` | `/testengine/sessions/{id}/next-question/` | Keyingi javobsiz savol |
| `POST` | `/testengine/sessions/{id}/sync/` | Offline to'plangan javoblarni bir so'rovda yuklash |

#### Test varaqasi

`questions/` javobi — har bir savol uchun: `order`, `question` (matn, variantlar, rasm, qiyinlik), `my_answer`, `is_answered`.

Barcha savollar bir marta yuklanadi, front ularni xotirada saqlaydi va sahifama-sahifa ko'rsatadi.

> **`correct_option` yakunlashgacha qaytarilmaydi.** Foydalanuvchi to'g'ri belgilaganini bilolmaydi.

#### ✅ Orqaga qaytish va javobni to'g'rilash

Bu to'liq qo'llab-quvvatlanadi:

| Foydalanuvchi qiladi | So'rov | Server qiladi |
|---|---|---|
| 3-savolda **B** ni belgiladi | `POST .../questions/3/answer/` | Javobni saqlaydi, natija ko'rsatmaydi |
| 10-savolda edi, 3-savolga qaytdi | *hech narsa* — savol xotirada | — |
| 3-savolda **B → C** ga o'zgartirdi | `POST .../questions/3/answer/` | Eski yozuvni **yangilaydi**, dublikat yaratmaydi |
| Tanlovni butunlay olib tashladi | `DELETE .../questions/3/answer/` | Javob o'chadi, savol yana «javobsiz» bo'ladi |

**Javob berishda yuboriladi:** `selected_option` (bitta harf), ixtiyoriy `confidence` (`sure`/`guess`) va `time_spent_seconds`.

Savollar tartibi va ro'yxati sessiya davomida **o'zgarmaydi** — 3-savolga qaytganda aynan o'sha savol chiqadi.

#### `progress` — navigatsiya paneli va taymer

**Javobda:** `total_questions`, `answered_count`, `unanswered_count`, `unanswered_orders`, `is_finished`, ⚠️ `seconds_left`, ⚠️ `expires_at`

`unanswered_orders` — bo'sh qolgan savollarning tartib raqamlari. Pastdagi `1 2 3 … 30` panelida qizil nuqta qo'yish uchun.

#### Imtihon taymeri

`mode: exam` da server `expires_at` qo'yadi — har bir savolga 90 soniya (30 savol = 45 daqiqa).

- Front taymerni `seconds_left` dan yuritadi, lekin **haqiqat serverda**
- Telefon vaqtini o'zgartirish yoki taymerni to'xtatish foyda bermaydi
- Vaqt tugagach javob yuborilsa **400** qaytadi
- Har qanday so'rovda server muddatni tekshiradi va o'tgan bo'lsa sessiyani **avtomatik yakunlaydi**
- Foydalanuvchi umuman qaytmasa ham sessiya fon vazifasi bilan yopiladi

#### Offline sinxronizatsiya

`sync/` — internet uzilganda front javoblarni telefonda to'playdi, aloqa tiklanganda hammasini bir so'rovda yuboradi. **Takroriy yuborish xavfsiz** — javoblar yangilanadi, dublikat bo'lmaydi.

---

### 5.3. Yakunlash va tahlil

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `POST` ⚠️ | `/testengine/sessions/{id}/finish/` | **Testni yakunlash** — natija va to'liq tahlil bitta javobda |
| `GET` ⚠️ | `/testengine/sessions/{id}/review/` | Tahlilga keyin qaytish |

**Javobda:**
- `session` — sessiya ma'lumoti
- `result` — `total_score`, `correct_count`, `incorrect_count`, `unanswered_count`, `total_questions`, `accuracy_percent`, `duration_seconds`
- `review` — har bir savol: `order`, `question`, `correct_option`, `selected_option`, `is_correct`, `is_answered`, `time_spent_seconds`, ⚠️ `hint`, ⚠️ `explanation`
- ⚠️ `explanation_access` — izohlar ochiqmi va nega

**Yechim izohi obunaga bog'liq:**

| Daraja | `correct_option` | `explanation` |
|---|---|---|
| Guest | — (natija umuman yo'q) | `null` |
| Free | ✅ ochiq | `null`, `code: upgrade_required` |
| Pro-Basic | ✅ ochiq | ✅ kuniga N ta test |
| Pro-Full | ✅ ochiq | ✅ cheksiz |

Xato savol ostida **«Nega xato? → Pro'da ochiladi 🔒»** tugmasini `explanation_access` ga qarab chiqaring.

> Izoh limiti **sessiya bo'yicha** hisoblanadi — bir testning tahlilini qayta-qayta ochish limitni yemaydi.

Yakunlashda avtomatik ishlaydi: takrorlash kartalari ochiladi, streak yangilanadi, XP beriladi, reyting va liga hisoblanadi, yutuqlar tekshiriladi.

> Bo'sh test uchun XP ham, reyting ham berilmaydi — sessiya ochib darrov yakunlash orqali «farming» qilib bo'lmaydi.

---

### 5.4. Sessiyalar

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` | `/testengine/sessions/` | Mening sessiyalarim ro'yxati |
| `POST` ⚠️ | `/testengine/sessions/` | Fan bo'yicha aralash sessiya (bir necha mavzudan) |
| `GET` ⚠️ | `/testengine/sessions/{id}/` | Sessiya tafsiloti |
| `PATCH` | `/testengine/sessions/{id}/` | Yakunlanmagan sessiyada rejimni almashtirish |
| `DELETE` | `/testengine/sessions/{id}/` | Sessiyani o'chirish |

⚠️ **Sessiya javobiga yangi maydonlar qo'shildi:** `topic`, `grade`, `time_limit_seconds`, `expires_at`, `seconds_left`, `auto_finished`

⚠️ `POST /testengine/sessions/` — endi ikkita yangi xato bo'lishi mumkin: **403** `daily_topic_limit_reached` va **400** `question_count_exceeded` (tarif ruxsat bergan sondan ko'p so'ralsa).

**Filtrlar:** `?subject=` · `?mode=` · `?is_finished=` · `?started_at_after=` · `?started_at_before=` · `?finished_at_after=` · `?finished_at_before=`

---

### 5.5. Javoblar (savol ID bo'yicha)

Bu endpointlar `order` o'rniga savol `id` si bilan ishlaydi — offline va bulk holatlar uchun.

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` | `/testengine/sessions/{session_id}/answers/` | Sessiyadagi barcha javoblarim |
| `POST` | `/testengine/sessions/{session_id}/answers/` | Javob berish (`question` id si bilan) |
| `POST` | `/testengine/sessions/{session_id}/answers/bulk/` | Ko'p javobni bir so'rovda saqlash |
| `GET` | `/testengine/sessions/{session_id}/answers/{answer_id}/` | Bitta javob |
| `DELETE` | `/testengine/sessions/{session_id}/answers/{answer_id}/` | Javobni o'chirish |

**Filtrlar:** `?question=` · `?is_correct=` · `?confidence=` · `?time_spent_min=` · `?time_spent_max=`

---

### 5.6. Natijalar

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` | `/testengine/results/` | Natijalar ro'yxati |
| `GET` | `/testengine/results/my-results/` | Faqat mening natijalarim |
| `GET` | `/testengine/results/{id}/` | Bitta natija tafsiloti |

**Filtrlar:** `?session=` · `?total_score_min=` · `?total_score_max=`

---

### 5.7. Xatolar banki 🆕

Ilgari natija ekranini yopgandan keyin xato qilingan savol yo'qolib ketardi. Endi ular bir joyda to'planadi.

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` 🆕 | `/testengine/mistakes/` | **Xato qilingan savollarim** (sahifalangan) |
| `POST` 🆕 | `/testengine/mistakes/start-test/` | **Aynan o'sha xatolardan yangi test ochish** |

**Filtrlar:** `?subject=` · `?topic=`

**`start-test` da yuboriladi:** `count`, `subject`, `topic` — uchalasi ham ixtiyoriy. Javobda oddiy sessiya keladi, keyin mavjud test ekranidan foydalaniladi.

> **Faqat oxirgi javob hisobga olinadi.** Savolni keyinchalik to'g'ri yechgan bo'lsangiz, u bankdan avtomatik chiqib ketadi.
>
> **Kunlik mavzu limiti bu yerda qo'llanilmaydi** — xatoni tuzatish yangi mavzu ochish emas. Limit tugagan foydalanuvchi ham xatolari ustida ishlay oladi.

**Xato:** 400 `no_mistakes` — bank bo'sh. Xabarda «Avval test ishlang» deb yoziladi.

---

### 5.8. Guest oqimi 🆕 🔓

Ro'yxatdan o'tmagan foydalanuvchi ham test ishlay oladi, lekin **qat'iy 20 ta savol** bilan va **natijasini ko'rmasdan**. Bazada hech qanday yozuv yaratilmaydi — butun sessiya imzolangan token ichida yuradi.

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` 🆕 🔓 | `/testengine/guest/topics/` | Guest ishlashi mumkin bo'lgan mavzular |
| `POST` 🆕 🔓 | `/testengine/guest/start/` | **Testni boshlash** — 20 ta savol birdaniga |
| `POST` 🆕 🔓 | `/testengine/guest/submit/` | **Yakunlash → ro'yxatdan o'tish taklifi** |

#### `guest/topics/`
Faqat kamida 20 ta savoli bor mavzular chiqadi — «ochdim, savol yo'q ekan» holati bo'lmaydi.
Filtrlar: `?subject=` · `?grade=`. Har bir qatorda `question_count` har doim 20 (guestda tanlov yo'q).

#### `guest/start/`
**Yuboriladi:** faqat `topic`.
**Javobda:** `token`, `question_count` (20), `questions` (barchasi birdaniga), `topic`, `subject`, `is_guest`, `notice`.

- `token` ni saqlab qo'ying — yakunlashda kerak bo'ladi. **3 soat** amal qiladi
- `notice` — ekranda ko'rsatiladigan tayyor ogohlantirish matni
- Savollarda `correct_option` **yo'q**

#### `guest/submit/`
**Yuboriladi:** `token` va `answers` ro'yxati.
Javoblar qabul qilinadi, lekin **baholanmaydi va saqlanmaydi**.

**Javobda natija emas, taklif keladi:**
`requires_registration`, `results_hidden`, `title`, `detail`, `actions`, `total_questions`, `answered_count`, `code: registration_required`

`actions` da ikkita tugma tayyor keladi — matnlari ham javobda, front ularni o'zi yozmaydi:
- `register` — «Ro'yxatdan o'tish» (asosiy)
- `later` — «Keyinroq»

> **Ball, foiz, to'g'ri javoblar soni — hech biri qaytmaydi.**
> «Keyinroq» bosilganda ham natija ochilmaydi: bu faqat oynani yopadi.

**Xatolar:** 400 `invalid_token` (token soxta yoki buzilgan) · 400 `token_expired` (3 soatdan oshgan)

---

## 6. PROGRESS — `/progress/`

**9 ta yo'l · 9 ta operatsiya**

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` | `/progress/reviews/` | Takrorlash kartalarim ro'yxati |
| `GET` | `/progress/reviews/today/` | **Bugun takrorlash kerak bo'lgan kartalar** |
| `POST` | `/progress/reviews/{id}/submit/` | Takrorlash javobini yuborish |
| `GET` | `/progress/streak/` | Streak holati |
| `POST` | `/progress/streak/freeze/` | Streak «muz»ini ishlatish |
| `GET` | `/progress/xp/summary/` | XP yig'indisi |
| `GET` | `/progress/xp/transactions/` | XP tarixi |
| `GET` 🆕 | `/progress/achievements/` | **Yutuqlar** |
| `GET` ⚠️ | `/progress/leaderboard/weekly/` | Haftalik leaderboard — **eskirgan** |

### Takrorlash kartalari

Xato qilingan savollar avtomatik takrorlash deckiga tushadi. Karta ochilgandan keyin uni qayta yechish kerak; to'g'ri javob berilsa interval uzayadi va vaqti kelib deckdan chiqadi.

`submit/` da yuboriladi: javob to'g'ri/xato va sarflangan vaqt. Tez javob kartani uzoqroqqa suradi, sekin javob — yaqinroqqa.

**Filtrlar:** `?question=` · `?next_review_date=` · `?next_review_date_after=` · `?next_review_date_before=`

### Streak
**Javobda:** `current_streak`, `longest_streak`, `last_activity_date`, `freezes_available`
Kun chegarasi **mahalliy yarim tunda**. `freeze/` — bir kunni o'tkazib yuborganda streakni saqlab qolish uchun.

### XP
`xp/summary/` javobida: `xp_total`, `xp_today`, `xp_this_week`
`xp/transactions/` — har bir XP yozuvining sababi bilan. Filtr: `?source=` (`test` · `streak` · `review` · `bonus`)

### Yutuqlar 🆕

**Javobda:** `unlocked_count`, `total_count`, `results`

Har bir qatorda: `code`, `name`, `description`, `icon` (emoji), `metric`, `threshold`, `current_value`, `progress_percent`, `xp_reward`, `is_unlocked`, `unlocked_at`

> **Qulflangan nishonlar ham keladi** — `progress_percent` bilan. «100 tadan 73 tasi» ko'rsatkichi nishonning o'zidan kuchliroq motivatsiya beradi.
> Tartib: qo'lga kiritilganlar birinchi, keyin eng yaqinlari.
> Bazada 19 ta nishon bor; admin yangisini qo'shsa u avtomatik chiqadi.

### ⚠️ `leaderboard/weekly/` — eskirgan

Ishlaydi va javob shakli o'zgarmadi, lekin endi `/rating/leaderboard/weekly/` bilan **bir xil manbadan** o'qiydi.

> **Yangi ekranlarda `/rating/leaderboard/weekly/` ni ishlating** — u `my_position` ni ham qaytaradi.
> Ilgari bu ikkalasi butunlay boshqa tartib berardi va foydalanuvchi «mening o'rnim nechinchi?» degan savolga ikki xil javob olardi.

---

## 7. REYTING — `/rating/`

**11 ta yo'l · 11 ta operatsiya**

> **Ikkita ko'rsatkich ajratilgan va ular bir-birini almashtira olmaydi:**
> **⭐ daraja (0–5)** — «qanchalik bilaman». Savol qiyinligiga bog'liq, javobsiz savol ham hisobga kiradi, kam ma'lumotda o'rtachaga tortiladi.
> **XP** — «qancha ishladim». Leaderboard va ligalar aynan shu bo'yicha saralanadi.

### 7.1. Shaxsiy daraja

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` ⚠️ | `/rating/me/` | Mening reytingim. `?period=daily` / `weekly` / `all_time` |
| `GET` ⚠️ | `/rating/subjects/` | Fanlar bo'yicha darajam |
| `GET` | `/rating/subjects/{subject_id}/` | Bitta fan bo'yicha |
| `GET` ⚠️ | `/rating/topics/` | Mavzular bo'yicha darajam |
| `GET` | `/rating/topics/{topic_id}/` | Bitta mavzu bo'yicha |
| `GET` | `/rating/history/` | Reyting o'zgarishlari tarixi |
| `GET` 🆕 | `/rating/weak-topics/` | **Eng ko'p qiynalayotgan mavzularim** |

**`me/` javobida:** `period`, `stars`, ⚠️ `xp`, `rank`, `tests_completed`, `correct_answers`, `incorrect_answers`, ⚠️ `unanswered_answers`, `accuracy_percentage`, ⚠️ `completion_percentage`, `period_start_date`, `period_end_date`

⚠️ `accuracy_percentage` — javob berilganlar ichida to'g'rilik foizi.
⚠️ `completion_percentage` — savollarning qancha ulushiga umuman javob berilgan. Ikkalasi alohida ko'rsatilishi kerak: 100% aniqlik bilan 20 tadan 5 tasiga javob bergan odam bilan hammasiga javob bergan odam bir xil ko'rinmasligi kerak.

**`topics/` javobida qo'shimcha:** ⚠️ `needs_practice` — bu mavzu ustida ishlash kerakmi.

### `weak-topics/` 🆕

Profil ekranidagi «Zaif mavzularingiz» bo'limi shundan quriladi, har bir qator yonida «Mashq qilish» tugmasi turadi.

**Parametr:** `?limit=` — standart 10, maksimum 50

**Javobda:** `topic`, `topic_name`, `subject_id`, `subject_name`, `grade_id`, `grade_name`, `stars`, `accuracy_percentage`, `correct_answers`, `incorrect_answers`, `answered_count`, `can_start_test`

> `can_start_test` `false` bo'lsa tugmani o'chirib qo'ying — o'sha mavzuda hali yetarli savol yo'q.
> Bitta testdagi omadsizlik «zaif mavzu» hisoblanmaydi: kamida 10 ta javob to'plangan mavzular chiqadi.

---

### 7.2. Leaderboard

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` ⚠️ | `/rating/leaderboard/{period}/` | **Top-50.** `period`: `daily` · `weekly` · `all_time` |

⚠️ **Javob shakli o'zgardi.** Ilgari to'g'ridan-to'g'ri massiv kelardi, endi obyekt:

**Javobda:** `period`, `period_start_date`, `period_end_date`, `results`, `my_position`

`results` ichidagi har bir qator: `rank`, `user_id`, `full_name`, ⚠️ `avatar_url`, ⚠️ `xp`, `stars`, `tests_completed`, `is_current_user`

`my_position`: `rank`, `total_participants`, `in_top`

> **Saralash endi XP bo'yicha**, yulduz bo'yicha emas.
> Top-50 ga kirmasangiz ham `my_position` da o'z o'rningizni ko'rasiz — «4 821 kishidan 137-o'rin».
> **Email hech qachon qaytmaydi.** Ismi kiritilmagan foydalanuvchi «Anonim» bo'lib ko'rinadi.

**Xato:** 400 — `period` noto'g'ri bo'lsa.

---

### 7.3. Ligalar 🆕

Global top-50 o'rniga **30 kishilik haftalik guruhlar**. Sabab: 10 000 foydalanuvchida top-50 ro'yxati 9 950 kishi uchun mavjud emasdek — ular o'z o'rnini ko'rmaydi va reyting ular uchun ishlamaydi. 30 kishilik guruhda esa har kim o'z o'rnini ko'radi.

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` 🆕 | `/rating/league/` | **Mening haftalik ligam** va guruhdagi to'liq tartib |
| `GET` 🆕 | `/rating/league/tiers/` | Daraja nomlari va guruh qoidalari |
| `GET` 🆕 | `/rating/league/history/` | O'tgan haftalardagi natijalarim |

#### `league/` — reyting ekranining asosiy so'rovi

**Javobda:** `has_league`, `tier`, `tier_name`, `group_number`, `period_start_date`, `period_end_date`, `league_size`, `promote_count`, `demote_count`, `my_rank`, `my_xp`, `my_zone`, `standings`

`standings` ichidagi har bir qator: `rank`, `user_id`, `full_name`, `avatar_url`, `xp`, `zone`, `is_current_user`

**Zonalar — front rangi uchun:**

| `zone` | Ma'nosi | O'rin |
|---|---|---|
| `promotion` | Keyingi darajaga ko'tariladi | 1–7 |
| `safe` | O'z darajasida qoladi | o'rta |
| `demotion` | Oldingi darajaga tushadi | oxirgi 5 |

**Darajalar:** Bronza (1) → Kumush (2) → Oltin (3) → Platina (4) → Olmos (5)
Bronzadan pastga tushilmaydi, Olmosdan yuqoriga chiqilmaydi. Hafta dushanba 00:05 da yakunlanadi.

> Bu hafta hali test ishlanmagan bo'lsa `has_league: false` keladi va `detail` da tayyor matn bo'ladi: «Birinchi testdan keyin ligaga qo'shilasiz». `standings` bo'sh bo'ladi.
> **Email hech qachon qaytmaydi**, ismsiz foydalanuvchi «Anonim».

#### `league/tiers/`
Barcha daraja nomlari va qoidalar. Ikonkalar va «qanday ishlaydi» oynasi uchun — bir marta yuklab keshga qo'ysa bo'ladi.
**Javobda:** `tiers` (`value` + `name`), `league_size` (30), `promote_count` (7), `demote_count` (5)

#### `league/history/`
Oxirgi 20 ta hafta. Har bir qatorda: `period_start_date`, `period_end_date`, `tier`, `tier_name`, `rank`, `xp`, `outcome` (`promoted` · `stayed` · `demoted`), `outcome_display` (o'zbekcha tayyor matn).

---

## 8. OBUNA VA TO'LOV — `/billing/`

**12 ta yo'l · 17 ta operatsiya**

### 8.1. Tariflar

| Metod | Yo'l | Vazifasi | Kim |
|---|---|---|---|
| `GET` | `/billing/plan/` | Tariflar ro'yxati (Free, Pro-Basic, Pro-Full) | Hamma |
| `POST` | `/billing/plan/` | Yangi tarif yaratish | Admin |
| `GET` | `/billing/plan/{id}/` | Bitta tarif | Hamma |
| `PUT` `PATCH` | `/billing/plan/{id}/` | Narx va cheklovlarni o'zgartirish | Admin |
| `DELETE` | `/billing/plan/{id}/` | Tarifni o'chirish | Admin |

**Tarif maydonlari:** `code`, `name` (+tarjimalari), `description`, `price`, `duration_days`, `is_active`, `is_pro`, `daily_topic_limit`, `max_question_count`, `can_view_explanations`, `explanation_limit_per_day`, `features`

> Narx ham, cheklovlar ham **kodda emas** — admin panelda boshqariladi. `daily_topic_limit` bo'sh bo'lsa cheklov yo'q.

### 8.2. Obunalar

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` | `/billing/subscriptions/eligibility/` | **Qaysi tarifga o'ta olaman** — tarif ekranining asosiy so'rovi |
| `GET` | `/billing/subscriptions/current/` | Joriy faol obunam |
| `GET` | `/billing/subscriptions/` | Obunalarim tarixi |
| `PATCH` | `/billing/subscriptions/{id}/cancel/` | Obunani bekor qilish |

`eligibility/` — har bir tarif uchun: bosiladigan tugmami yoki «X sanagacha kutiladi» deb ko'rsatiladimi. Javobda `can_request`, `reason_code`, `reason` (tayyor matn), `available_at`, `is_upgrade`.

> **Qoida:** faol obuna davomida ayni yoki arzonroq tarifni qayta olib bo'lmaydi — muddat tugashini kutish kerak.
> Qimmatroq tarifga (upgrade) istalgan paytda o'tish mumkin va eski obunaning qolgan kunlari yangisiga qo'shiladi.

### 8.3. To'lov arizalari

Hozircha to'lov shlyuzi yo'q: foydalanuvchi tarif tanlab ariza yuboradi, admin Telegram orqali bog'lanadi va to'lovni qabul qilgach arizani tasdiqlaydi.

| Metod | Yo'l | Vazifasi | Kim |
|---|---|---|---|
| `GET` | `/billing/payments/info/` | To'lov ma'lumotlari va admin bilan bog'lanish havolasi | Hamma |
| `GET` | `/billing/payments/` | Mening arizalarim | Hamma |
| `POST` | `/billing/payments/` | **Obuna arizasi yuborish** | Hamma |
| `GET` | `/billing/payments/{id}/` | Bitta ariza | Hamma |
| `PATCH` | `/billing/payments/{id}/cancel/` | Arizani qaytarib olish (tasdiqlanmagan bo'lsa) | Hamma |
| `PATCH` | `/billing/payments/{id}/approve/` | Arizani tasdiqlash → obuna faollashadi | Admin |
| `PATCH` | `/billing/payments/{id}/reject/` | Arizani rad etish (sababi bilan) | Admin |

**Ariza yuborishda:** `plan`, ixtiyoriy `contact_phone`, `contact_telegram`, `note`

> Bepul tarif uchun admin tasdig'i kutilmaydi — obuna darhol faollashadi.

**Xato kodlari:** `already_active` · `downgrade_blocked` · `pending_request` · `plan_inactive` · `already_reviewed`

---

## 9. BILDIRISHNOMALAR — `/notifications/`

**5 ta yo'l · 6 ta operatsiya**

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` | `/notifications/my/` | Mening bildirishnomalarim (sahifalangan) |
| `GET` | `/notifications/unread-count/` | O'qilmaganlar soni — **badge uchun** |
| `POST` | `/notifications/mark-read/` | Hammasini o'qilgan deb belgilash |
| `POST` | `/notifications/mark-read/{id}/` | Bittasini o'qilgan deb belgilash |
| `GET` | `/notifications/announcements/` | E'lonlar ro'yxati |
| `POST` | `/notifications/announcements/` | E'lon yuborish — barcha foydalanuvchilarga tarqaladi (Admin) |

**Bildirishnoma turlari:**
`welcome` (ro'yxatdan o'tish tabrigi) · `rating_up` (reyting ko'tarilishi, liga natijasi, yangi yutuq) · `announcement` (umumiy e'lon) · `sub_approved` · `sub_rejected` · `sub_expiring` · `test_finished`

Har bir yozuvda: `id`, `type`, `message`, `is_read`, `created_at`

---

## 10. DASHBOARD — `/dashboard/`

**10 ta yo'l · 12 ta operatsiya**

### 10.1. Mentor paneli

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` | `/dashboard/mentor/summary/` | Mentor panelining umumiy ko'rinishi: o'quvchilar soni, faollik, ochiq ogohlantirishlar |
| `GET` | `/dashboard/mentor/students/` | Mening o'quvchilarim ro'yxati |
| `POST` | `/dashboard/mentor/students/` | O'quvchini o'ziga biriktirish |
| `PATCH` | `/dashboard/mentor/students/{id}/` | Biriktirilgan o'quvchi ma'lumotini yangilash |
| `GET` | `/dashboard/mentor/students/{student_id}/stats/` | **Bitta o'quvchining to'liq statistikasi**: testlar, aniqlik, zaif mavzular, faollik |
| `GET` | `/dashboard/mentor/alerts/` | Ogohlantirishlar ro'yxati (masalan: o'quvchi uzoq vaqt kirmadi) |
| `POST` | `/dashboard/mentor/alerts/` | Qo'lda ogohlantirish yaratish |
| `PATCH` | `/dashboard/mentor/alerts/{id}/resolve/` | Ogohlantirishni yopish |

### 10.2. Admin paneli

| Metod | Yo'l | Vazifasi |
|---|---|---|
| `GET` | `/dashboard/admin/summary/` | Platformaning umumiy ko'rsatkichlari: foydalanuvchilar, testlar, obunalar, daromad |
| `GET` | `/dashboard/admin/analytics/` | Analitika yozuvlari ro'yxati (kunlik/haftalik/oylik kesimlar) |
| `GET` | `/dashboard/admin/analytics/{id}/` | Bitta analitika yozuvi |
| `GET` | `/dashboard/admin/access-log/` | Panelga kirish jurnali — kim, qachon, qayerdan kirgan |

---

## 11. XATO KODLARI

Har bir xato javobida `detail` (o'zbekcha tayyor matn) bor. Front matnni o'zi yozmaydi.

| Kod | HTTP | Qachon | Front nima qiladi |
|---|---|---|---|
| `daily_topic_limit_reached` | **403** | Free foydalanuvchi kunlik 4 ta mavzu limitiga yetdi | **Pro taklifi oynasi.** «Ertaga 00:00» ni `reset_at` dan oling |
| `not_enough_questions` | 400 | Mavzuda 20 tadan kam savol | «Bu mavzuda hozircha savol yetarli emas» |
| `invalid_count` | 400 | Tanlangan son bosqichlar ro'yxatida yo'q | Bosqich tugmalarini qayta yuklash |
| `question_count_exceeded` | 400 | Tarif ruxsat bergan sondan ko'p so'raldi | Pro taklifi |
| `no_mistakes` | 400 | Xatolar banki bo'sh | «Avval test ishlang» — bo'sh holat ekrani |
| `session_expired` | 409 | Imtihon vaqti tugagan | Natija ekraniga o'tkazish |
| `invalid_token` | 400 | Guest tokeni soxta yoki buzilgan | Guest testni qaytadan boshlash |
| `token_expired` | 400 | Guest tokeni 3 soatdan oshgan | Guest testni qaytadan boshlash |
| `registration_required` | 200 | Guest testni yakunladi | **Ro'yxatdan o'tish oynasi**, tugmalar `actions` dan |
| `upgrade_required` | 200 | Yechim izohi tarifda yo'q | Izoh o'rniga «Pro'da ochiladi 🔒» tugmasi |
| `explanation_limit_reached` | 200 | Kunlik izoh limiti tugagan | «Bugungi izoh limitingiz tugadi» |
| `already_active` | 400 | Bu tarif allaqachon faol | Tarif ekranidagi xabar |
| `downgrade_blocked` | 400 | Arzonroq tarifga o'tib bo'lmaydi | «X sanagacha kutiladi» |
| `pending_request` | 400 | Ariza allaqachon ko'rib chiqilmoqda | «Admin javobini kuting» |
| `plan_inactive` | 400 | Tarif hozircha mavjud emas | Tugmani o'chirish |

---

## 12. EKRAN → SO'ROV XARITASI

| Ekran | So'rovlar |
|---|---|
| **Kirish** | `POST /api/auth/google/` → tokenlarni saqlash |
| **Bosh sahifa** | 🆕 `GET /testengine/my-limits/` · `GET /progress/streak/` · `GET /progress/xp/summary/` · `GET /notifications/unread-count/` |
| **Fan tanlash** | `GET /catalog/subjects/` |
| **Sinf tanlash** | 🆕 `GET /catalog/grades/?subject=` |
| **Mavzu tanlash** | `GET /catalog/topics/?grade=&has_test=true` |
| **Savol soni tanlash** | 🆕 `GET /testengine/topics/{id}/available-counts/` |
| **Testni boshlash** | 🆕 `POST /testengine/topics/{id}/start-test/` |
| **Test ekrani** | `GET /testengine/sessions/{id}/questions/` — bir marta, hammasi birdaniga |
| **Javob berish / o'zgartirish** | `POST /testengine/sessions/{id}/questions/{order}/answer/` |
| **Tanlovni bekor qilish** | `DELETE /testengine/sessions/{id}/questions/{order}/answer/` |
| **Navigatsiya paneli va taymer** | `GET /testengine/sessions/{id}/progress/` |
| **Yakunlash** | `POST /testengine/sessions/{id}/finish/` |
| **Natija va tahlil** | `finish` javobidagi `review` va `explanation_access` |
| **Tahlilga qaytish** | `GET /testengine/sessions/{id}/review/` |
| **Reyting ekrani** | 🆕 `GET /rating/league/` · `GET /rating/leaderboard/weekly/` |
| **Profil va progress** | `GET /rating/me/` · 🆕 `GET /rating/weak-topics/` · 🆕 `GET /progress/achievements/` |
| **Xatolar ustida ishlash** | 🆕 `GET /testengine/mistakes/` → 🆕 `POST /testengine/mistakes/start-test/` |
| **Takrorlash** | `GET /progress/reviews/today/` → `POST /progress/reviews/{id}/submit/` |
| **Bildirishnomalar** | `GET /notifications/my/` → `POST /notifications/mark-read/` |
| **Obuna ekrani** | `GET /billing/subscriptions/eligibility/` → `POST /billing/payments/` |
| **Guest oqimi** | 🆕 `GET /testengine/guest/topics/` → 🆕 `POST /testengine/guest/start/` → 🆕 `POST /testengine/guest/submit/` |
| **Mentor paneli** | `GET /dashboard/mentor/summary/` · `GET /dashboard/mentor/students/` |
| **Admin paneli** | `GET /dashboard/admin/summary/` · `GET /dashboard/admin/analytics/` |

---

## YANGI VA O'ZGARGAN — QISQACHA

### 🆕 Yangi qo'shilgan (15 ta yo'l, 19 ta operatsiya)

| Guruh | Yo'llar |
|---|---|
| Sinf / Kitob | `/catalog/grades/` · `/catalog/grades/{id}/` |
| Test boshlash | `/testengine/topics/{id}/available-counts/` · `/testengine/topics/{id}/start-test/` · `/testengine/my-limits/` |
| Guest | `/testengine/guest/topics/` · `/testengine/guest/start/` · `/testengine/guest/submit/` |
| Xatolar banki | `/testengine/mistakes/` · `/testengine/mistakes/start-test/` |
| Ligalar | `/rating/league/` · `/rating/league/tiers/` · `/rating/league/history/` |
| Zaif mavzular | `/rating/weak-topics/` |
| Yutuqlar | `/progress/achievements/` |

### ⚠️ O'zgarganlar — frontend albatta o'qisin

| Endpoint | Nima o'zgardi |
|---|---|
| `POST /catalog/topics/` | Endi `subject` emas, **`grade`** yuboriladi |
| `GET /catalog/topics/` | Yangi: `grade`, `grade_name`, `has_test`, `available_counts`, `question_count`. Yangi filtrlar: `?grade=`, `?has_test=` |
| `GET /catalog/subjects/` | Yangi: `grade_count`, `topic_count`, `has_test` |
| `GET /rating/leaderboard/{period}/` | **Javob shakli o'zgardi:** massiv emas, `results` + `my_position`. Saralash endi **XP bo'yicha** |
| `GET /rating/me/` va `/rating/topics/` | Yangi: `xp`, `unanswered_answers`, `completion_percentage`, `needs_practice` |
| `POST .../finish/` va `GET .../review/` | Yangi: `explanation_access`, har bir savolga `explanation` va `hint` |
| Sessiya endpointlari | Yangi: `topic`, `grade`, `time_limit_seconds`, `expires_at`, `seconds_left`, `auto_finished` |
| `POST /testengine/sessions/` | Yangi xatolar: **403** `daily_topic_limit_reached`, **400** `question_count_exceeded` |
| `GET /progress/leaderboard/weekly/` | **Eskirgan** — yangi ekranlarda `/rating/leaderboard/weekly/` ishlatilsin |
