"""Test natijasini ballga aylantirish — YAGONA manba.

Nega alohida modul: bir xil hisob uch joyda kerak bo'ladi — reyting
(`rating`), XP (`progress`) va natija ekrani (`testengine`). Formula uch
joyda takrorlansa, ular albatta bir-biridan ajralib ketadi.

Ikkita ko'rsatkich ATAYIN ajratilgan:

* **Ball (points)** -> ⭐ daraja. "Men qanchalik bilaman". Qiyinlikka
  bog'liq, javobsiz savol ham hisobga kiradi.
* **XP** -> leaderboard. "Men qancha ishladim". Hajmga bog'liq.

Ular bir-birini almashtira olmaydi: faqat aniqlik bo'yicha reyting qursak,
5 ta savolga javob berib 100% olgan odam 600 ta savol ishlagan odamdan
yuqori turadi; faqat hajm bo'yicha qursak, tasodifiy tugma bosgan odam
g'olib bo'ladi.
"""

from __future__ import annotations

from catalog.models import Question

# Qiyinlik og'irligi. Qiyin savolni yechish oson savolni yechishdan
# qimmatroq bo'lishi kerak — aks holda foydalanuvchi eng oson mavzuni
# aylantirib reyting yig'adi.
DIFFICULTY_WEIGHT = {
    Question.Difficulty.VERY_EASY: 0.6,
    Question.Difficulty.EASY: 0.8,
    Question.Difficulty.MEDIUM: 1.0,
    Question.Difficulty.HARD: 1.3,
    Question.Difficulty.VERY_HARD: 1.6,
}
DEFAULT_WEIGHT = 1.0

# ⭐ hisobida "ishonch" tuzatmasi. Bu — Bayes yumshatishi: kam ma'lumotda
# baho o'rtachaga (0.5) tortiladi.
#
# Nega kerak: busiz 5 ta savolga javob berib hammasini to'g'ri topgan odam
# darhol 5.0 ⭐ oladi va 600 ta savol ishlagan, 90% aniqlikdagi odamdan
# yuqori chiqadi. PRIOR_WEIGHT ~ ikkita 20 savolli testga teng.
PRIOR_WEIGHT = 40.0
PRIOR_RATIO = 0.5

MAX_STARS = 5.0

# XP: bitta to'g'ri javobning bazaviy qiymati (qiyinlikka ko'paytiriladi).
XP_PER_CORRECT = 10
# Testni OXIRIGACHA yechganlik uchun bonus. Yarim tashlab ketilgan testdan
# ko'ra tugatilgani qadrli.
XP_COMPLETION_BONUS = 5
# Testdagi savollarning kamida shuncha ulushiga javob berilsa "tugatilgan"
# hisoblanadi.
COMPLETION_THRESHOLD = 0.8


def difficulty_weight(difficulty) -> float:
    try:
        return DIFFICULTY_WEIGHT.get(int(difficulty), DEFAULT_WEIGHT)
    except (TypeError, ValueError):
        return DEFAULT_WEIGHT


class SessionScore:
    """Bitta sessiyaning ball hisobi.

    `possible` ga sessiyadagi BARCHA savollar kiradi — javob berilmaganlari
    ham. Aynan shu javobsiz savolni "bepul" bo'lishdan saqlaydi: aks holda
    eng yaxshi strategiya 30 ta savoldan faqat 5 tasiga javob berib qolganini
    bo'sh qoldirish bo'lardi.
    """

    __slots__ = (
        'earned', 'possible', 'correct_count', 'incorrect_count',
        'unanswered_count', 'total_questions', 'xp',
    )

    def __init__(self, earned=0.0, possible=0.0, correct_count=0,
                 incorrect_count=0, unanswered_count=0, total_questions=0, xp=0):
        self.earned = earned
        self.possible = possible
        self.correct_count = correct_count
        self.incorrect_count = incorrect_count
        self.unanswered_count = unanswered_count
        self.total_questions = total_questions
        self.xp = xp

    @property
    def ratio(self) -> float:
        return (self.earned / self.possible) if self.possible else 0.0

    @property
    def accuracy_percent(self) -> float:
        answered = self.correct_count + self.incorrect_count
        if not answered:
            return 0.0
        return round(self.correct_count / answered * 100, 2)

    def as_dict(self) -> dict:
        return {
            'earned_points': round(self.earned, 4),
            'possible_points': round(self.possible, 4),
            'correct_count': self.correct_count,
            'incorrect_count': self.incorrect_count,
            'unanswered_count': self.unanswered_count,
            'total_questions': self.total_questions,
            'xp': self.xp,
        }


def score_session(session, answers=None, session_questions=None) -> SessionScore:
    """Sessiyani ballga aylantiradi.

    `answers` va `session_questions` berilsa qayta so'rov qilinmaydi —
    `finish_session` ularni allaqachon o'qigan bo'ladi.
    """
    from testengine.models import Answer, SessionQuestion

    if session_questions is None:
        session_questions = list(
            SessionQuestion.objects
            .filter(session=session)
            .select_related('question')
            .order_by('order')
        )
    if answers is None:
        answers = list(Answer.objects.filter(session=session).select_related('question'))

    answer_by_question = {answer.question_id: answer for answer in answers}

    earned = 0.0
    possible = 0.0
    correct_count = incorrect_count = unanswered_count = 0
    xp = 0

    for item in session_questions:
        weight = difficulty_weight(item.question.difficulty)
        possible += weight

        answer = answer_by_question.get(item.question_id)
        if answer is None:
            unanswered_count += 1
        elif answer.is_correct:
            correct_count += 1
            earned += weight
            xp += round(XP_PER_CORRECT * weight)
        else:
            incorrect_count += 1

    total_questions = len(session_questions)

    # Sessiyada savollar qotirilmagan bo'lsa (eski yozuvlar, to'g'ridan-to'g'ri
    # yaratilgan sessiya) javoblarning o'zidan hisoblaymiz.
    if not total_questions and answers:
        for answer in answers:
            weight = difficulty_weight(answer.question.difficulty)
            possible += weight
            if answer.is_correct:
                correct_count += 1
                earned += weight
                xp += round(XP_PER_CORRECT * weight)
            else:
                incorrect_count += 1
        total_questions = len(answers)

    answered = correct_count + incorrect_count
    if total_questions and answered / total_questions >= COMPLETION_THRESHOLD:
        xp += XP_COMPLETION_BONUS

    return SessionScore(
        earned=earned,
        possible=possible,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        unanswered_count=unanswered_count,
        total_questions=total_questions,
        xp=xp,
    )


def score_from_result(result) -> SessionScore:
    """`TestResult` dan ball hisobi.

    Avval sessiyaning haqiqiy savollari bo'yicha hisoblanadi. Agar sessiyada
    savol ham, javob ham topilmasa (testlarda `TestResult` to'g'ridan-to'g'ri
    yaratilishi mumkin) — natijadagi sonlardan o'rtacha og'irlik bilan
    taxminiy hisob chiqariladi, aks holda XP umuman berilmay qolardi.
    """
    score = score_session(result.session)
    if score.total_questions:
        return score

    correct = result.correct_count
    incorrect = result.incorrect_count
    unanswered = result.unanswered_count
    total = correct + incorrect + unanswered
    if not total:
        return score

    xp = correct * XP_PER_CORRECT
    answered = correct + incorrect
    if answered / total >= COMPLETION_THRESHOLD:
        xp += XP_COMPLETION_BONUS

    return SessionScore(
        earned=float(correct),
        possible=float(total),
        correct_count=correct,
        incorrect_count=incorrect,
        unanswered_count=unanswered,
        total_questions=total,
        xp=xp,
    )


def stars_from_points(earned, possible) -> float:
    """To'plangan balldan ⭐ daraja (0–5).

    Bayes yumshatishi bilan: kam ma'lumotda baho o'rtachaga tortiladi va
    faqat haqiqiy hajm bilan 5.0 ga yaqinlashadi. Shuning uchun 5.0 ni
    "olish" emas, "qozonish" kerak.
    """
    possible = max(float(possible or 0), 0.0)
    earned = max(float(earned or 0), 0.0)
    if possible <= 0:
        return 0.0

    adjusted = (earned + PRIOR_RATIO * PRIOR_WEIGHT) / (possible + PRIOR_WEIGHT)
    return round(max(0.0, min(1.0, adjusted)) * MAX_STARS, 2)


def raw_accuracy(earned, possible) -> float:
    """Yumshatilmagan aniqlik foizi — foydalanuvchiga ⭐ yonida ko'rsatish uchun."""
    possible = float(possible or 0)
    if possible <= 0:
        return 0.0
    return round(max(0.0, min(1.0, float(earned or 0) / possible)) * 100, 2)
