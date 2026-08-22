# TestYourself — DTM Test platformasi

DTM testlariga tayyorgarlik uchun Django + DRF backend: test yechish, takrorlash
kartalari (spaced repetition), XP/streak, reyting va leaderboard, obuna/to'lov,
mentor paneli.

## Texnologiyalar

| Qatlam | Texnologiya |
|---|---|
| Framework | Django 6.0, Django REST Framework |
| Baza | PostgreSQL |
| Kesh / throttling / broker | Redis |
| Fon vazifalari | Celery |
| Autentifikatsiya | Google OAuth + Apple ID + JWT (SimpleJWT) |
| Tillar | O'zbekcha (asosiy), Ruscha, Inglizcha |
| API hujjatlari | drf-spectacular |
| Statik fayllar | WhiteNoise |
| Admin panel | django-unfold |

## Lokal ishga tushirish

Kerak: Python 3.12, PostgreSQL, Redis.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # qiymatlarni to'ldiring
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Fon vazifalari uchun alohida terminalda (`--beat` obuna muddatlarini kunlik
tozalab turadi):

```bash
celery -A config worker --beat --loglevel=info
```

Worker ishga tushirishni xohlamasangiz, `.env` da `CELERY_TASK_ALWAYS_EAGER=True`
qo'ying — vazifalar so'rov ichida bajariladi (faqat development uchun).

### SECRET_KEY generatsiya qilish

```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

> `.env` fayllarida `#` belgisi izoh boshlanishi deb hisoblanadi. Kalitni
> qo'shtirnoqsiz yozing va tarkibida `#` bo'lmasligiga ishonch hosil qiling,
> aks holda qiymat kesilib qoladi.

## Testlar

```bash
python manage.py test
```

Testlar ishlashi uchun PostgreSQL va Redis ishlab turishi kerak (kesh va
throttling shularga bog'liq).

## Deploy (Render)

Repoda `render.yaml` bor — Render'da "New → Blueprint" orqali web servis,
Postgres va Redis birga yaratiladi.

Qo'lda sozlanganda:

- **Build command:** `./build.sh`
- **Start command:** `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120`
- **Worker (alohida servis):** `celery -A config worker --loglevel=info`

### Majburiy muhit o'zgaruvchilari

To'liq ro'yxat va izohlar — [.env.example](.env.example).

| O'zgaruvchi | Izoh |
|---|---|
| `SECRET_KEY` | Har bir muhit uchun alohida generatsiya qilinadi |
| `DEBUG` | Prodda **doim** `False` |
| `ALLOWED_HOSTS` | Vergul bilan ajratilgan domenlar |
| `CSRF_TRUSTED_ORIGINS` | Proxy ortida admin login uchun majburiy, `https://` bilan |
| `CORS_ALLOWED_ORIGINS` | Frontend domeni — qo'shilmasa SPA backendga ulanolmaydi |
| `DATABASE_URL` | Render Postgres beradi |
| `REDIS_URL` | **Majburiy** — kesh, throttling va Celery shunga bog'liq |
| `GOOGLE_CLIENT_ID` | Google OAuth (Android / web) |
| `APPLE_CLIENT_IDS` | Apple ID (iPhone / iPad). Bo'sh bo'lsa Apple login o'chiq |
| `ADMIN_TELEGRAM_LINK` | "Admin bilan bog'lanish" havolasi |
| `TELEGRAM_BOT_TOKEN` | Arizani adminga avtomatik yuborish uchun (ixtiyoriy) |
| `TELEGRAM_ADMIN_CHAT_ID` | Arizalar tushadigan chat (ixtiyoriy) |

### Deploydan oldingi tekshiruv

```bash
DEBUG=False python manage.py check --deploy
```

Xavfsizlik ogohlantirishlari (`security.W*`) chiqmasligi kerak.

## API hujjatlari

| Manzil | Izoh |
|---|---|
| `/swagger/` | Swagger UI |
| `/redoc/` | ReDoc |
| `/schema/` | OpenAPI sxemasi (YAML) |

Prodda (`DEBUG=False`) bu sahifalar **faqat admin** uchun ochiq.

## Loyiha tuzilishi

| App | Vazifasi |
|---|---|
| `account` | Foydalanuvchilar, Google OAuth, JWT |
| `catalog` | Fanlar, mavzular, savollar |
| `testengine` | Test sessiyalari, javoblar, natijalar |
| `progress` | Takrorlash kartalari, streak, XP |
| `rating` | Reytinglar va leaderboard |
| `billing` | Tariflar, obunalar, to'lovlar |
| `notifications` | Bildirishnomalar va e'lonlar |
| `dashboard` | Mentor paneli va analitika |
| `common` | Umumiy model, permission, pagination, throttle |

## Asosiy oqimlar

### Test topshirish — javobni oxirigacha o'zgartirish mumkin

Sessiya ochilganda savollar ro'yxati **qotiriladi**, shuning uchun
foydalanuvchi 10-savoldan 3-savolga qaytib javobini almashtira oladi.
To'g'ri/noto'g'ri ma'lumoti **`finish` gacha umuman qaytarilmaydi**.

```
POST   /testengine/sessions/                          {subject, question_count: 15}
GET    /testengine/sessions/<id>/questions/           butun varaqa + mening javoblarim
GET    /testengine/sessions/<id>/questions/3/         3-savol
POST   /testengine/sessions/<id>/questions/3/answer/  javob berish / O'ZGARTIRISH
DELETE /testengine/sessions/<id>/questions/3/answer/  tanlovni bekor qilish
GET    /testengine/sessions/<id>/progress/            nechta javobsiz qoldi
GET    /testengine/sessions/<id>/next-question/       keyingi javobsiz savol
POST   /testengine/sessions/<id>/finish/              natija + to'liq tahlil
GET    /testengine/sessions/<id>/review/              tahlilni qayta ko'rish
POST   /testengine/sessions/<id>/sync/                offline javoblarni yuklash
```

`finish` dan keyin javoblar qotib qoladi: har qanday o'zgartirish `400`
qaytaradi.

### Obuna — ariza va admin tasdig'i

Tariflar narxi bo'yicha taqqoslanadi (masalan 0 / 50 000 / 70 000 so'm):

* Bepul tarif — admin kutilmaydi, darhol faollashadi.
* Pullik tarif — ariza `pending` bo'ladi, adminga Telegramga xabar ketadi,
  javobda "Admin bilan bog'lanish" havolasi (oldindan to'ldirilgan xabar
  bilan) qaytadi. Admin tasdiqlagach obuna faollashadi.
* Aktiv obuna davomida **ayni yoki arzonroq** tarifni qayta olib bo'lmaydi —
  muddat tugashi kerak (`code=already_active` / `downgrade_blocked`,
  `available_at` bilan).
* **Qimmatroq** tarifga istalgan paytda o'tish mumkin; eski obunaning qolgan
  kunlari yangisiga qo'shiladi.

```
GET    /billing/plan/                          tariflar ro'yxati
GET    /billing/subscriptions/eligibility/     har bir tarif bo'yicha holat
POST   /billing/payments/                      ARIZA yuborish
PATCH  /billing/payments/<id>/cancel/          o'z arizasini qaytarib olish
PATCH  /billing/payments/<id>/approve/         admin tasdiqlaydi
PATCH  /billing/payments/<id>/reject/          admin rad etadi (+ sabab)
GET    /billing/subscriptions/current/         joriy obuna (barqaror shakl)
```

### Kirish — telefon, planshet, brauzer

```
POST /api/auth/google/          Android va web
POST /api/auth/apple/           iPhone / iPad (Sign in with Apple)
POST /api/auth/refresh/         JWT yangilash
GET  /api/auth/me/              profil
PATCH /api/auth/me/             til va profilni tahrirlash
POST /api/auth/devices/         qurilmani (push token) ro'yxatdan o'tkazish
```

Bir email — bitta profil: Google bilan kirgan foydalanuvchi keyin Apple ID
bilan kirsa, o'sha profilga bog'lanadi.

> **CORS va mobil ilovalar.** Mahalliy (native) iOS/Android ilovalar `Origin`
> header yubormaydi, shuning uchun CORS ular uchun to'siq emas —
> `CORS_ALLOWED_ORIGINS` ga hech narsa qo'shish shart emas. Sozlama faqat
> brauzer va WebView (Capacitor/Ionic) mijozlariga tegishli; ular uchun
> `capacitor://`, `ionic://` va `localhost` allaqachon ruxsat etilgan.

### Tillar (uz / ru / en)

Kontent tarjimasi model ustunlarida saqlanadi (`name` / `name_ru` /
`name_en`), qo'shimcha kutubxona ishlatilmagan. So'rov tili quyidagi
tartibda aniqlanadi:

1. `?lang=ru`
2. `X-Language: ru`
3. foydalanuvchi profilidagi `language`
4. `Accept-Language`
5. `uz`

Tarjima kiritilmagan bo'lsa o'zbekchasi qaytadi — mijozda bo'sh matn
chiqmaydi. Variant kalitlari (A/B/C) barcha tillarda bir xil bo'lishi
majburiy, aks holda savol saqlanmaydi.

### Savol rasmi (ixtiyoriy)

Savolga rasm biriktirish mumkin, lekin **majburiy emas**:

```bash
# Rasmsiz — oddiy JSON
curl -X POST /catalog/questions/ -H 'Content-Type: application/json' -d '{...}'

# Rasm bilan — multipart
curl -X POST /catalog/questions/ -F topic=1 -F text='...' \
     -F 'options={"A":"...","B":"..."}' -F correct_option=A -F image=@grafik.png
```

Chegara: 5 MB. Rasmni olib tashlash uchun `PATCH` da `image: null`.

## Ma'lum cheklovlar

- **Savol rasmlari va media.** `Question.image` lokal diskka (`MEDIA_ROOT`)
  yoziladi va Django orqali `/media/...` da beriladi. Render'da disk
  vaqtinchalik — **redeploy'da yuklangan rasmlar yo'qoladi**. Ishlab
  chiqarishda S3 yoki Cloudinary'ga o'tish kerak (`STORAGES['default']` ni
  almashtirish yetarli, model va API o'zgarmaydi).
- **To'lovlar qo'lda tasdiqlanadi.** Telegram orqali; avtomatik to'lov shlyuzi
  (Payme/Click) va webhook hozircha yo'q. `Payment.Provider` da o'rin
  qoldirilgan.
- **Push xabarnomalar.** Qurilmalar va push tokenlar saqlanadi
  (`/api/auth/devices/`), lekin FCM/APNs ga yuborish hali ulanmagan.
- **Admin logotipi.** `static/images/logo.png` qo'shilmagan — admin panelda
  logotip o'rnida bo'sh joy ko'rinadi.
