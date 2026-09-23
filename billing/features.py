"""Tarif imkoniyatlari katalogi — ptichkalar ro'yxatining YAGONA manbasi.

Nega alohida modul: admin panel (frontend) tarif yaratganda qaysi ptichka va
qaysi raqam maydonlari borligini shu yerdan o'qiydi (`GET /billing/plan/features/`).
Ro'yxat kodda bitta joyda tursa, yangi cheklov qo'shilganda frontendga tegilmaydi
— u ro'yxatni aylanib formani o'zi chizadi.

Bu yerda TARIFLAR yo'q. «Basic», «Pro», «Premium» degan nomlar kodda umuman
yozilmaydi: admin nechta tarif xohlasa shuncha yaratadi, nomini o'zi qo'yadi va
quyidagi ptichkalardan keraklisini belgilaydi.

Har bir yozuv:

* ``key``    — `Plan` maydoni nomi yoki `Plan.features` JSON kaliti;
* ``storage``— 'field' (modelda alohida maydon) yoki 'feature' (JSON ichida);
* ``kind``   — 'flag' (ptichka), 'limit' (raqam) yoki 'choice' (ro'yxatdan tanlash);
* ``unlimited_when_empty`` — raqam bo'sh qoldirilsa cheksiz degani (0 = yopiq);
* ``enforced``— backend uni HOZIR tekshiradimi. `False` bo'lsa ptichka bor, lekin
  ortidagi kod hali yozilmagan — frontend uni "tez kunda" deb ko'rsatishi mumkin.
"""

from __future__ import annotations

from common.i18n import DEFAULT_LANGUAGE

# Guruhlar — admin panelda ptichkalar shu sarlavhalar ostida chiqadi.
GROUPS = [
    {'key': 'test', 'label': {'uz': 'Test ishlash', 'ru': 'Прохождение тестов', 'en': 'Taking tests'}},
    {'key': 'explanation', 'label': {'uz': 'Yechim izohlari', 'ru': 'Разборы решений', 'en': 'Explanations'}},
    {'key': 'practice', 'label': {'uz': 'Xato ustida ishlash', 'ru': 'Работа над ошибками', 'en': 'Practice'}},
    {'key': 'analytics', 'label': {'uz': 'Tahlil va statistika', 'ru': 'Аналитика', 'en': 'Analytics'}},
    {'key': 'motivation', 'label': {'uz': 'Motivatsiya', 'ru': 'Мотивация', 'en': 'Motivation'}},
    {'key': 'extra', 'label': {'uz': "Qo'shimcha", 'ru': 'Дополнительно', 'en': 'Extras'}},
]


PLAN_FEATURES = [
    # --- Test ishlash -----------------------------------------------------
    {
        'key': 'daily_topic_limit',
        'storage': 'field',
        'kind': 'limit',
        'group': 'test',
        'unlimited_when_empty': True,
        'enforced': True,
        'label': {
            'uz': 'Kunlik mavzu limiti',
            'ru': 'Дневной лимит тем',
            'en': 'Daily topic limit',
        },
        'help': {
            'uz': "Bir kunda nechta TURLI mavzuda test ishlay oladi. "
                  "Bo'sh qoldirilsa — cheksiz.",
            'ru': "Сколько РАЗНЫХ тем в день. Пусто — без ограничений.",
            'en': "How many DIFFERENT topics per day. Empty means unlimited.",
        },
    },
    {
        'key': 'max_question_count',
        'storage': 'field',
        'kind': 'choice',
        'group': 'test',
        'unlimited_when_empty': False,
        'enforced': True,
        'label': {
            'uz': 'Bir testdagi maksimal savol',
            'ru': 'Максимум вопросов в тесте',
            'en': 'Max questions per test',
        },
        'help': {
            'uz': "Foydalanuvchi shu songacha savol tanlay oladi.",
            'ru': "До этого количества вопросов можно выбрать.",
            'en': "The user can pick up to this many questions.",
        },
    },
    {
        'key': 'can_choose_question_count',
        'storage': 'field',
        'kind': 'flag',
        'group': 'test',
        'enforced': True,
        'label': {
            'uz': "Savol sonini o'zi tanlaydi",
            'ru': 'Сам выбирает число вопросов',
            'en': 'Chooses question count',
        },
        'help': {
            'uz': "O'chirilsa test har doim eng kichik to'plam (20 ta) bilan boshlanadi.",
            'ru': "Если выключено — всегда минимальный набор (20).",
            'en': "If off, tests always start with the smallest set (20).",
        },
    },
    {
        'key': 'can_use_exam_mode',
        'storage': 'field',
        'kind': 'flag',
        'group': 'test',
        'enforced': True,
        'label': {
            'uz': 'Imtihon rejimi (vaqt chegarasi bilan)',
            'ru': 'Режим экзамена (с таймером)',
            'en': 'Exam mode (timed)',
        },
        'help': {
            'uz': "O'chirilsa faqat «O'rganish» rejimida test ishlaydi.",
            'ru': "Если выключено — доступен только режим практики.",
            'en': "If off, only practice mode is available.",
        },
    },

    # --- Yechim izohlari --------------------------------------------------
    {
        'key': 'can_view_explanations',
        'storage': 'field',
        'kind': 'flag',
        'group': 'explanation',
        'enforced': True,
        'label': {
            'uz': "Yechim izohlarini ko'radi",
            'ru': 'Видит разборы решений',
            'en': 'Can view explanations',
        },
        'help': {
            'uz': "Test yakunida to'g'ri javob va izohni ochish huquqi.",
            'ru': "Доступ к разбору после теста.",
            'en': "Access to the worked solution after a test.",
        },
    },
    {
        'key': 'explanation_limit_per_day',
        'storage': 'field',
        'kind': 'limit',
        'group': 'explanation',
        'unlimited_when_empty': True,
        'enforced': True,
        'label': {
            'uz': 'Kunlik izoh limiti',
            'ru': 'Дневной лимит разборов',
            'en': 'Daily explanation limit',
        },
        'help': {
            'uz': "Kuniga nechta TESTNING izohini ocha oladi. Bo'sh — cheksiz, "
                  "0 — umuman ochilmaydi.",
            'ru': "Сколько тестов в день можно разобрать. Пусто — без лимита, 0 — нельзя.",
            'en': "How many tests per day can be reviewed. Empty means unlimited, 0 means none.",
        },
    },

    # --- Xato ustida ishlash ----------------------------------------------
    {
        'key': 'mistake_test_daily_limit',
        'storage': 'field',
        'kind': 'limit',
        'group': 'practice',
        'unlimited_when_empty': True,
        'enforced': True,
        'label': {
            'uz': 'Xatolardan test tuzish (kuniga)',
            'ru': 'Тест из ошибок (в день)',
            'en': 'Mistake tests per day',
        },
        'help': {
            'uz': "Xatolar bankidan kuniga nechta test tuza oladi. Bo'sh — cheksiz, "
                  "0 — faqat xatolar ro'yxatini ko'radi.",
            'ru': "Сколько тестов из банка ошибок в день. Пусто — без лимита, 0 — только просмотр.",
            'en': "Tests generated from the mistake bank per day. Empty means unlimited, 0 means view only.",
        },
    },
    {
        'key': 'review_cards_daily_limit',
        'storage': 'field',
        'kind': 'limit',
        'group': 'practice',
        'unlimited_when_empty': True,
        'enforced': True,
        'label': {
            'uz': 'Takrorlash kartalari (kuniga)',
            'ru': 'Карточки повторения (в день)',
            'en': 'Review cards per day',
        },
        'help': {
            'uz': "Kuniga nechta takrorlash kartasini yecha oladi. Bo'sh — cheksiz, "
                  "0 — takrorlash yopiq.",
            'ru': "Сколько карточек в день. Пусто — без лимита, 0 — недоступно.",
            'en': "Review cards per day. Empty means unlimited, 0 disables reviews.",
        },
    },

    # --- Tahlil -----------------------------------------------------------
    {
        'key': 'can_view_analytics',
        'storage': 'field',
        'kind': 'flag',
        'group': 'analytics',
        'enforced': True,
        'label': {
            'uz': 'Zaif mavzular va batafsil tahlil',
            'ru': 'Слабые темы и детальная аналитика',
            'en': 'Weak topics and detailed analytics',
        },
        'help': {
            'uz': "O'chirilsa faqat umumiy ball va daraja ko'rinadi.",
            'ru': "Если выключено — только общий балл и уровень.",
            'en': "If off, only the overall score and level are shown.",
        },
    },
    {
        'key': 'history_days',
        'storage': 'field',
        'kind': 'limit',
        'group': 'analytics',
        'unlimited_when_empty': True,
        'enforced': True,
        'label': {
            'uz': 'Natijalar tarixi (kun)',
            'ru': 'История результатов (дней)',
            'en': 'Result history (days)',
        },
        'help': {
            'uz': "Necha kunlik natijani ko'ra oladi. Bo'sh — butun tarix.",
            'ru': "За сколько дней видна история. Пусто — вся история.",
            'en': "How many days of history are visible. Empty means all of it.",
        },
    },

    # --- Motivatsiya ------------------------------------------------------
    {
        'key': 'streak_freezes_per_month',
        'storage': 'field',
        'kind': 'limit',
        'group': 'motivation',
        'unlimited_when_empty': True,
        'enforced': True,
        'label': {
            'uz': 'Streak muzlatish (oyiga)',
            'ru': 'Заморозка серии (в месяц)',
            'en': 'Streak freezes per month',
        },
        'help': {
            'uz': "Kun o'tkazib yuborsa, ketma-ketlikni saqlab qoluvchi «muz». "
                  "Bo'sh — cheksiz, 0 — yo'q.",
            'ru': "«Заморозка» серии при пропуске дня. Пусто — без лимита, 0 — нет.",
            'en': "Keeps the streak alive on a missed day. Empty means unlimited, 0 means none.",
        },
    },

    # --- Qo'shimcha imkoniyatlar ------------------------------------------
    {
        'key': 'mock_exam',
        'storage': 'feature',
        'kind': 'flag',
        'group': 'extra',
        'enforced': True,
        'label': {
            'uz': 'DTM blok imtihoni',
            'ru': 'Пробный экзамен ДТМ',
            'en': 'Full mock exam',
        },
        'help': {
            'uz': "Bir nechta fan ketma-ket, bitta umumiy taymer bilan — "
                  "real imtihon tartibida.",
            'ru': "Несколько предметов подряд с общим таймером.",
            'en': "Several subjects in a row under one shared timer.",
        },
    },
    {
        'key': 'ai_tutor',
        'storage': 'feature',
        'kind': 'flag',
        'group': 'extra',
        'enforced': False,
        'label': {
            'uz': 'AI tutor',
            'ru': 'AI-репетитор',
            'en': 'AI tutor',
        },
        'help': {
            'uz': "Savolga moslab yechimni tushuntiradi. HOZIRCHA ISHLAMAYDI — "
                  "ulash joyi tayyor, LLM chaqiruvi keyin yoziladi "
                  "(`testengine/explanations.py`).",
            'ru': "Объясняет решение под конкретный вопрос. ПОКА НЕ РАБОТАЕТ — "
                  "место для подключения готово.",
            'en': "Explains the solution for the question. NOT ACTIVE YET — "
                  "the integration point is ready.",
        },
    },
    {
        'key': 'export_results',
        'storage': 'feature',
        'kind': 'flag',
        'group': 'extra',
        'enforced': True,
        'label': {
            'uz': 'Natijalarni Excel qilib yuklab olish',
            'ru': 'Выгрузка результатов в Excel',
            'en': 'Export results to Excel',
        },
        'help': {
            'uz': "Natijalar tarixi `.xlsx` fayl bo'lib yuklanadi.",
            'ru': "История результатов выгружается файлом .xlsx.",
            'en': "The result history downloads as an .xlsx file.",
        },
    },
    {
        'key': 'mentor_support',
        'storage': 'feature',
        'kind': 'flag',
        'group': 'extra',
        'enforced': True,
        'label': {
            'uz': 'Mentor nazorati',
            'ru': 'Поддержка ментора',
            'en': 'Mentor supervision',
        },
        'help': {
            'uz': "Talabani mentorga biriktirish mumkin bo'ladi. Ptichkasiz "
                  "talabani mentorga bog'lab bo'lmaydi.",
            'ru': "Ученика можно закрепить за ментором.",
            'en': "The student can be assigned to a mentor.",
        },
    },
    {
        'key': 'priority_support',
        'storage': 'feature',
        'kind': 'flag',
        'group': 'extra',
        'enforced': True,
        'label': {
            'uz': "Prioritet qo'llab-quvvatlash",
            'ru': 'Приоритетная поддержка',
            'en': 'Priority support',
        },
        'help': {
            'uz': "Telegramda navbatsiz javob. Bu tashkiliy va'da — kod faqat "
                  "ariza sahifasida shuni ko'rsatadi.",
            'ru': "Ответ вне очереди в Telegram. Код лишь показывает это в заявке.",
            'en': "Faster replies in Telegram; the code only surfaces it on the request page.",
        },
    },
]


FEATURE_KEYS = [item['key'] for item in PLAN_FEATURES]
FIELD_FEATURE_KEYS = [i['key'] for i in PLAN_FEATURES if i['storage'] == 'field']
JSON_FEATURE_KEYS = [i['key'] for i in PLAN_FEATURES if i['storage'] == 'feature']


def _text(block, language) -> str:
    return block.get(language) or block.get(DEFAULT_LANGUAGE) or ''


def feature_catalog(language=DEFAULT_LANGUAGE) -> dict:
    """Admin panel formasi uchun tayyor ro'yxat.

    `choices` faqat kerak bo'lganda hisoblanadi — savol sonlari
    `testengine` da belgilangan, bu yerda takrorlanmaydi.
    """
    from testengine.models import QUESTION_COUNT_TIERS

    items = []
    for item in PLAN_FEATURES:
        entry = {
            'key': item['key'],
            'storage': item['storage'],
            'kind': item['kind'],
            'group': item['group'],
            'enforced': item['enforced'],
            'label': _text(item['label'], language),
            'help': _text(item['help'], language),
        }
        if item['kind'] == 'limit':
            entry['unlimited_when_empty'] = item.get('unlimited_when_empty', True)
        if item['key'] == 'max_question_count':
            entry['choices'] = list(QUESTION_COUNT_TIERS)
        items.append(entry)

    return {
        'groups': [
            {'key': group['key'], 'label': _text(group['label'], language)}
            for group in GROUPS
        ],
        'features': items,
    }
