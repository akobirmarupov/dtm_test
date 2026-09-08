# DTM Test Platformasi — To'liq Texnik Topshiriq (AI Coding Agent uchun Prompt)

> Ushbu hujjatni Claude Code (yoki boshqa AI coding agent)ga to'g'ridan-to'g'ri vazifa sifatida berishingiz mumkin. Loyiha stack: **Django + DRF** (backend allaqachon mavjud: `account`, `billing`, `catalog`, `dashboard`, `progress`, `testengine` app'lari bor).

---

## 1. Loyiha haqida umumiy tushuncha

DTM (Davlat Test Markazi uslubidagi) test tayyorlash platformasi. Foydalanuvchilar fan bo'yicha, sinf bo'yicha, mavzu bo'yicha test ishlaydi. Tizim ro'yxatdan o'tgan va o'tmagan foydalanuvchilar uchun turli cheklovlarga ega, shuningdek Pro obuna orqali qo'shimcha imkoniyatlar beradi.

---

## 2. Ma'lumotlar tuzilishi (Content Hierarchy)

Iyerarxiya qat'iy tartibda: **Fan → Sinf/Kitob → Mavzu → Savollar (Test bazasi)**

### 2.1. Fan (Subject)
- Admin tomonidan qo'lda yaratiladi. Masalan: *Matematika*, *Fizika*, *Ingliz tili*.
- Mavjud model: `catalog.Subject` (agar mavjud bo'lmasa yaratilsin).

### 2.2. Sinf / Kitob (Grade / Book) — Fanning ichida
- Fan tanlangandan so'ng, o'sha fanga tegishli "sinf" yoki "kitob" qo'lda yaratiladi.
- Bu shunchaki raqamli sinf bo'lishi shart emas — masalan:
  - `1-sinf`, `2-sinf`, ... `9-sinf` (standart maktab sinflari)
  - Yoki maxsus kitob nomi: masalan *"Matematika — Milliy sertifikat uchun"*, *"Uzb tili — Abituriyentlar uchun"*
- Ya'ni bu model aslida **"Sinf/Bo'lim" (Grade/Level)** deb nomlanishi kerak — erkin matn (free text) bilan yaratiladi, faqat raqamli sinf bilan cheklanmaydi.
- **Model taklifi:** `catalog.Grade` (fields: `subject` FK, `name` CharField, `order` IntegerField — tartiblash uchun).

### 2.3. Mavzu (Topic)
- Admin: Fanni tanlaydi → Sinfni/Kitobni tanlaydi (masalan: Matematika → 7-sinf) → Mavzu yaratadi (masalan: *"Qisqa ko'paytirish formulalari"*).
- **Model:** mavjud `catalog.Topic` (FK: `grade` ga bog'lansin, `grade` esa `subject`ga bog'liq bo'ladi — shu orqali fan avtomatik aniqlanadi).

### 2.4. Savollar / Testlar (Questions)
- Har bir mavzuga cheklanmagan sonda savol qo'shish mumkin (admin xohlagancha).
- Mavjud: `catalog.Question` (options, correct_option — bular allaqachon serializer'da bor).

**Iyerarxiya sxemasi:**
```
Subject (Matematika)
 └─ Grade (7-sinf)
     └─ Topic (Qisqa ko'paytirish formulalari)
         └─ Question x N (admin xohlagancha qo'shadi)
```

---

## 3. Test ishlash — savollar sonini tanlash logikasi

Bu eng muhim biznes-logika qismi.

### 3.1. Ruxsat etilgan "tier"lar (bosqichlar)
```python
QUESTION_COUNT_TIERS = [20, 25, 30, 35, 40, 45, 50, 55, 60]  # MAX = 60
```

### 3.2. Qoida
- Foydalanuvchi **umumiy savollar sonini hech qachon ko'rmaydi** — faqat nechta savol bilan test ishlashni tanlaydi.
- Mavzudagi jami savollar soniga qarab, faqat **shu songa yetadigan tier'lar** ko'rsatiladi:
  - Agar mavzuda **43 ta** savol bo'lsa → foydalanuvchiga faqat `20, 25, 30, 35, 40` ko'rsatiladi (45 ta yo'q, demak 45 chiqmaydi).
  - Agar mavzuda **45 yoki undan ko'p** savol bo'lsa → `45` ham qo'shiladi.
  - Agar **50 yoki undan ko'p** bo'lsa → `50` ham qo'shiladi. Va hokazo, 60 gacha.
- Minimal test ishlash uchun mavzuda kamida **20 ta savol** bo'lishi shart (aks holda test mavjud emas / "Hozircha yetarli savol yo'q" degan xabar chiqadi).

### 3.3. Algoritm (backend pseudocode)
```python
def get_available_tiers(total_questions: int) -> list[int]:
    TIERS = [20, 25, 30, 35, 40, 45, 50, 55, 60]
    if total_questions < 20:
        return []  # test mavjud emas
    return [t for t in TIERS if total_questions >= t]
```

### 3.4. Guest (ro'yxatdan o'tmagan) foydalanuvchi uchun maxsus qoida
- Guest ham test ishlay oladi, lekin **faqat 20 ta savol** bilan (tanlov yo'q, tier tanlash ko'rsatilmaydi, avtomatik 20).
- Guest uchun maksimal — 20 ta, undan ortiq umuman ishlay olmaydi.
- Guest natijalarini **ko'rmaydi** (savob/xato foizi, ball va h.k. yashiriladi).
- Guest uchun **hech narsa saqlanmaydi**: statistikaga, reytingga, tarixga yozilmaydi. Session tugagach hammasi yo'qoladi.

#### 3.4.1. Test tugagandan keyingi "Ro'yxatdan o'tish" taklifi (modal/oyna)
- Guest 20 ta savolni tugatgach, natija o'rniga **ro'yxatdan o'tishga taklif qiluvchi oyna (modal)** chiqadi.
- Bu oyna quyidagilarni ko'rsatishi kerak:
  - Ro'yxatdan o'tsa nimalar ochilishini qisqacha tushuntirish (masalan: *"Natijangizni ko'rish, xatolaringizni bilish, reytingda ishtirok etish va cheksiz test ishlash uchun ro'yxatdan o'ting"*).
  - Ikkita variant/tugma:
    1. **"Ro'yxatdan o'tish"** — darhol registratsiya oqimiga yo'naltiradi.
    2. **"Keyinroq"** — oyna yopiladi, foydalanuvchi bosh sahifaga qaytadi (natija baribir ko'rsatilmaydi, faqat ishlashni davom ettirishi yoki chiqib ketishi mumkin).
- **Muhim:** "Keyinroq" bosilganda ham guestga natija ochilib qolmasligi kerak — bu faqat oynani yopish, ro'yxatdan o'tish talabini bekor qilmaydi.

### 3.5. Ro'yxatdan o'tgan, lekin Pro bo'lmagan foydalanuvchi (Free)
- Yuqoridagi barcha tier'larni (mavzudagi savollar soniga qarab) tanlay oladi.
- Natijalar (to'g'ri/xato soni, ball) ko'rsatiladi.
- Statistikasi, XP'si, reytingi (`progress` app) yangilanadi va saqlanadi.
- **Kunlik mavzu limiti: 4 ta mavzu / kun.**
  - Cheklov **testlar soniga emas, balki mavzular soniga** qo'yiladi. Ya'ni bitta mavzuda xohlagancha test ishlashi mumkin (masalan bir mavzuda 5 marta test ishlasa, bu baribir "1 ta mavzu" hisoblanadi).
  - Kun davomida foydalanuvchi jami **4 ta turli mavzuda** test ishlay oladi. 5-mavzuga o'tishga urinsa — limit tugagani va ertaga (00:00 dan keyin) yangilanishi haqida xabar chiqadi.
  - Limit har kuni **00:00 (mahalliy vaqt, Toshkent/UZT)** da avtomatik tiklanadi (reset bo'ladi) — yangi kun uchun yana 4 ta yangi mavzu ochiladi.
  - Limit tugagan payt, foydalanuvchiga ham **Pro'ga o'tishni taklif qiluvchi oyna** chiqishi kerak (pastga qarang, 3.5.1).

#### 3.5.1. Limit tugaganda Pro taklifi (modal/oyna)
- Free foydalanuvchi kunlik 4-mavzu limitiga yetganda, 5-mavzuni tanlashga urinsa:
  - Oyna chiqadi: *"Bugungi kunlik limitingiz (4 ta mavzu) tugadi. Ertaga 00:00 dan keyin yangi mavzular ochiladi, yoki Pro sotib olib cheksiz mavzuda test ishlang."*
  - Tugmalar: **"Pro sotib olish"** va **"Keyinroq / Ertaga qaytaman"**.

### 3.6. Pro foydalanuvchi (Pro-Basic va Pro-Full — ikkalasi ham)
- Kunlik mavzu limiti **yo'q — cheksiz** mavzuda test ishlay oladi (Free'dagi 4 ta mavzu cheklovi Pro'ga tegishli emas).
- Tier tanlash, natija ko'rish, statistika — barchasi Free bilan bir xil ochiq, farq faqat xato tushuntirishlari darajasida (4-bo'limdagi jadvalga qarang).

---

## 4. Foydalanuvchi darajalari va cheklovlar (Feature Matrix)

Jami **4 xil holat** bo'ladi: Guest, Ro'yxatdan o'tgan (Free), Pro-Basic, Pro-Full.

| Imkoniyat | Guest | Free (ro'yxatdan o'tgan, pro emas) | Pro-Basic (35 000 so'm) | Pro-Full (59 000 so'm) |
|---|---|---|---|---|
| Test ishlash | Faqat 20 ta savol | 20–60 ta (mavjud tier bo'yicha) | 20–60 ta | 20–60 ta |
| Kunlik mavzu limiti | — (natija ko'rmaydi, ro'yxatdan o'tish taklif etiladi) | **4 ta mavzu/kun** (00:00 da reset), 5-chi mavzuda Pro taklif etiladi | Cheksiz | Cheksiz |
| Natija (ball, to'g'ri/xato soni) ko'rish | ❌ Yo'q | ✅ Bor | ✅ Bor | ✅ Bor |
| Statistika/tarix saqlanishi | ❌ Yo'q | ✅ Bor | ✅ Bor | ✅ Bor |
| Reytingda ishtirok | ❌ Yo'q | ✅ Bor (ko'ra oladi) | ✅ Bor | ✅ Bor |
| Xato qilingan savollar bo'yicha **tushuntirish** (hozircha AI'siz, keyinchalik AI orqali) | ❌ | ❌ | ⚠️ Cheklangan (masalan faqat to'g'ri javob ko'rsatiladi, tushuntirishsiz — aniq cheklov keyin belgilanadi) | ✅ To'liq (kelajakda AI ustoz tushuntiruvi bilan) |
| Boshqa cheklovlar (keyin aniqlanadi, masalan kunlik test soni, mavzular soni) | — | Bor bo'lishi mumkin | 1–2 ta cheklov | Cheklovsiz |

> **Eslatma:** Pro-Basic (35 000 so'm) uchun aniq 1-2 ta cheklov admin bilan kelishilgan holda keyinroq belgilanadi (masalan: kuniga faqat 3 marta batafsil natija ko'rish, yoki faqat oxirgi 5 ta xato uchun tushuntirish va h.k.). Pro-Full (59 000 so'm) — cheklovsiz, hammasi ochiq.

### 4.1. AI integratsiyasi (hozircha ishlatilmaydi, faqat struktura tayyorlansin)
- Pro (ayniqsa Pro-Full) foydalanuvchi xato qilgan savollar bo'yicha kelajakda **AI "ustoz"** orqali tushuntirish oladi.
- Hozircha AI ulanmaydi, lekin backend'da shu joy uchun **placeholder** qoldirilsin: masalan `ExplanationService` interfeysi yoki `explanation` maydoni (bo'sh/null) `AnswerResult` modelida — keyin osongina AI javobi bilan to'ldirish mumkin bo'lsin.

---

## 5. Obuna tizimi (Subscription / Billing)

- Loyihada allaqachon `billing` app mavjud — shu app kengaytirilsin.
- **3 xil reja:** Free, Pro-Basic, Pro-Full.
- **Narxlar qattiq kodlanmasin (hardcode qilinmasin)** — Django Admin panel orqali dinamik boshqariladi:
  - Admin `SubscriptionPlan` modelini yaratadi/tahrirlaydi: `name`, `price` (so'mda), `duration_days`, `features` (JSON yoki boolean flag'lar to'plami).
  - Default qiymatlar: Pro-Basic = 35 000 so'm, Pro-Full = 59 000 so'm — lekin admin istalgan vaqt buni 55 000, 75 000 va h.k.ga o'zgartira olishi kerak.
- **Model taklifi:**
```python
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)          # "Free", "Pro-Basic", "Pro-Full"
    price = models.PositiveIntegerField(default=0)   # so'mda
    duration_days = models.PositiveIntegerField(default=30)
    can_view_explanations = models.BooleanField(default=False)
    explanation_limit_per_day = models.PositiveIntegerField(null=True, blank=True)  # None = cheklovsiz
    is_active = models.BooleanField(default=True)
```

---

## 6. Reyting va statistika (`progress` app bilan bog'liq)

- Guest → reyting/statistikaga umuman kirmaydi.
- Free foydalanuvchi → reytingni **ko'ra oladi**, lekin xato tushuntirishlarisiz natija ko'radi.
- Pro foydalanuvchilar → reyting + to'liq natija tafsilotlari (Pro darajasiga qarab tushuntirish bilan yoki bo'lmasdan).
- `award_xp`, leaderboard cache invalidatsiyasi — mavjud tizim bilan mos ishlashi kerak (avvalgi backend o'zgarishlarida ko'rilgan `progress/services.py`).

---

## 6.1. Kunlik mavzu limiti — texnik logika (Free foydalanuvchilar uchun)

### Model taklifi
```python
class DailyTopicUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    date = models.DateField()  # UZT bo'yicha kun (00:00 dan 00:00 gacha)

    class Meta:
        unique_together = ("user", "topic", "date")
```

### Logika (pseudocode)
```python
DAILY_TOPIC_LIMIT = 4

def can_start_topic(user, topic):
    if user.is_pro:
        return True  # cheksiz

    today = timezone.localdate()  # Asia/Tashkent
    used_topics_today = DailyTopicUsage.objects.filter(
        user=user, date=today
    ).values("topic").distinct().count()

    # Agar bu mavzu bugun allaqachon ishlatilgan bo'lsa — yana ruxsat (cheklov mavzu SONIGA, testga emas)
    already_used = DailyTopicUsage.objects.filter(
        user=user, topic=topic, date=today
    ).exists()
    if already_used:
        return True

    return used_topics_today < DAILY_TOPIC_LIMIT

def register_topic_usage(user, topic):
    DailyTopicUsage.objects.get_or_create(
        user=user, topic=topic, date=timezone.localdate()
    )
```
- Reset avtomatik ishlaydi, chunki `date` bo'yicha filter qilinadi — alohida cron kerak emas, faqat `timezone.localdate()` **Asia/Tashkent** timezone'da to'g'ri ishlashini ta'minlash kerak (`settings.TIME_ZONE = "Asia/Tashkent"`).
- API darajasida: mavzuni tanlashda (`start-test`) shu tekshiruv ishlaydi; agar `can_start_topic() == False` bo'lsa — `403` yoki maxsus kod bilan javob qaytariladi (masalan `{"error": "daily_topic_limit_reached", "reset_at": "2026-09-08T00:00:00+05:00"}`), frontend shu asosda Pro-taklif oynasini chiqaradi.

---

## 7. Admin panel talablari

1. Fan (Subject) CRUD
2. Sinf/Kitob (Grade) CRUD — fanga bog'liq, erkin nom kiritish imkoniyati bilan
3. Mavzu (Topic) CRUD — grade'ga bog'liq
4. Savol (Question) CRUD — topic'ga bog'liq, variantlar va to'g'ri javob bilan
5. Obuna rejalari (SubscriptionPlan) CRUD — narx, muddat, cheklovlarni tahrirlash
6. Foydalanuvchilar ro'yxati — kim qaysi obunada ekanini ko'rish/o'zgartirish

---

## 8. Texnik amalga oshirish bo'yicha tavsiyalar

1. **Permission classes:** `IsGuestOrLimited`, `IsRegisteredFree`, `IsProBasic`, `IsProFull` kabi aniq DRF permission klasslar yarating — logika tarqoq bo'lib ketmasligi uchun.
2. **Tier hisoblash logikasi** alohida service funksiyasi sifatida yozilsin (`testengine/services.py` — `get_available_tiers()`), controller/view'da emas — test qilish oson bo'lishi uchun.
3. **Guest sessiyasi:** Guest uchun hech narsa DB'ga yozilmasligini ta'minlash uchun alohida oqim (flow) — masalan `AnonymousTestSession` umuman DB'da saqlanmaydi, faqat frontend/session-based hisoblash.
4. **Kesh:** Mavzudagi savollar sonini har safar hisoblamaslik uchun `topic.question_count` ni cache'lash yoki denormalizatsiya qilish tavsiya etiladi (savol qo'shilganda/o'chirilganda yangilanadi).
5. **Unit testlar:** `get_available_tiers()` funksiyasi uchun chegara holatlar (19, 20, 44, 45, 59, 60, 61 ta savol) bo'yicha testlar yozilsin.
6. **API dizayni:**
   - `GET /topics/{id}/available-counts/` → `{"tiers": [20,25,30,35,40]}` guest uchun `{"tiers": [20]}`
   - `POST /topics/{id}/start-test/` → `{"count": 30}`
7. **Feature flag tizimi:** Pro-Basic'dagi "1-2 cheklov" keyin osongina o'zgartirilishi uchun cheklovlarni kod ichida emas, `SubscriptionPlan.features` (JSON) orqali boshqaring.

---

## 9. Qo'shimcha tavsiyalar (mualliflik takliflari)

- **Progressiv test rejimi:** Foydalanuvchi tier tanlaganda, agar mavzuda masalan 62 ta savol bo'lsa, savollar tasodifiy (random) tanlansin — bir xil savollar takrorlanavermasligi uchun "so'nggi ishlagan savollarni kamroq takrorlash" logikasi qo'shilsa foydali bo'ladi.
- **Guest → Free konvertatsiya:** Guest test tugagach "Natijangizni ko'rish uchun ro'yxatdan o'ting" tugmasi bilan darhol ro'yxatdan o'tish oqimiga yo'naltirilsa, konversiya oshadi.
- **Pro muddati tugashi:** Pro tugagach avtomatik Free'ga qaytish (cron/celery job) va foydalanuvchiga oldindan bildirishnoma (masalan 3 kun qolganda) yuborilsa yaxshi bo'ladi.
- **To'lov tizimi:** O'zbekistonda odatda **Payme** yoki **Click** integratsiyasi kerak bo'ladi — `billing` app shu ikkalasiga moslashtirilishi tavsiya etiladi.
- **Analytics:** Qaysi mavzularda eng ko'p xato qilinayotgani bo'yicha admin uchun statistik dashboard (allaqachon `dashboard` app bor — shu yerga qo'shish mumkin) — bu keyinchalik AI tushuntirish tizimi uchun ham foydali ma'lumot bo'ladi.

---

## 10. AI Coding Agent uchun aniq topshiriq (TASK)

> Quyidagini Claude Code'ga to'g'ridan-to'g'ri berish uchun:

```
Yuqoridagi texnik topshiriqni o'qib chiq va quyidagi tartibda amalga oshir:
1. catalog app'da Grade modelini yarat (Subject FK, name, order) va migratsiya yoz.
2. Topic modelini Grade bilan bog'la (agar hozir Subject bilan bog'liq bo'lsa, migratsiya orqali o'zgartir).
3. testengine app'da get_available_tiers() service funksiyasini QUESTION_COUNT_TIERS = [20,25,30,35,40,45,50,55,60] asosida yoz va unit testlarini qo'sh.
4. Guest foydalanuvchi uchun cheklangan (faqat 20 ta, natijasiz, saqlanmaydigan) test oqimini alohida endpoint sifatida yoz.
5. Ro'yxatdan o'tgan foydalanuvchi uchun to'liq oqimni (tier tanlash, natija, statistika, reyting) yoz.
6. billing app'da SubscriptionPlan modelini narx/muddat/cheklovlar bilan yarat, admin panelga chiqar.
7. Pro-Basic va Pro-Full darajalari uchun permission va feature-flag mexanizmini qur.
8. Kelajakdagi AI tushuntirish integratsiyasi uchun ExplanationService interfeysini bo'sh implementatsiya bilan tayyorla (hozircha None qaytarsin).
Har bir qadamdan keyin mavjud kod bazasi (account, billing, catalog, dashboard, progress, testengine) bilan mosligini tekshir.
```

---

*Ushbu hujjat sizning loyihangiz talablarini tizimlashtirish uchun tayyorlangan. Agar Pro-Basic uchun aniq cheklovlar (masalan qancha marta tushuntirish ko'rish mumkinligi) hali qat'iy belgilanmagan bo'lsa, kod yozilishidan oldin buni aniqlashtirib olish tavsiya etiladi.*
