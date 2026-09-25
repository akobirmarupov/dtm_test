import random
from django.core.management.base import BaseCommand
from catalog.models import Subject, Grade, Topic, Question
from intro.models import IntroQuestion

SAMPLE_QUESTIONS_DATA = [
    # Matematika
    ("Matematika", "Algebra", "2x + 5 = 15 tenglamaning ildizini toping.", {"A": "x = 5", "B": "x = 10", "C": "x = 7", "D": "x = 4"}, "A", "2x = 10 -> x = 5"),
    ("Matematika", "Algebra", "y = x^2 - 4 funksiyaning nollarini toping.", {"A": "x = ±2", "B": "x = 2", "C": "x = ±4", "D": "x = 0"}, "A", "x^2 - 4 = 0 -> x = ±2"),
    ("Matematika", "Geometriya", "Teng yonli uchburchakning asosidagi burchagi 50° bo'lsa, uchidagi burchakni toping.", {"A": "80°", "B": "100°", "C": "50°", "D": "60°"}, "A", "180 - (50 + 50) = 80°"),
    ("Matematika", "Geometriya", "Kvadratning yuzi 64 sm² bo'lsa, uning perimetrini toping.", {"A": "32 sm", "B": "16 sm", "C": "64 sm", "D": "24 sm"}, "A", "a = 8, P = 4*8 = 32 sm"),
    ("Matematika", "Matematik analiz", "f(x) = 3x^2 + 2x hosilasini toping.", {"A": "6x + 2", "B": "3x + 2", "C": "6x^2", "D": "6x"}, "A", "f'(x) = 3*2x + 2 = 6x + 2"),
    
    # Fizika
    ("Fizika", "Mexanika", "Tezlik v = 20 m/s bo'lsa, 5 soniyada bosib o'tilgan yo'lni toping.", {"A": "100 m", "B": "4 m", "C": "25 m", "D": "50 m"}, "A", "S = v * t = 20 * 5 = 100 m"),
    ("Fizika", "Mexanika", "Nyutonning ikkinchi qonuni formulasini ko'rsating.", {"A": "F = m * a", "B": "F = m / a", "C": "E = mc^2", "D": "P = F / S"}, "A", "F = m * a"),
    ("Fizika", "Termodinamika", "Ideal gaz bosimi p va hajmi V ko'paytmasi nima deyiladi?", {"A": "Boyl-Mariott qonuni", "B": "Sharl qonuni", "C": "Gey-Lyussak qonuni", "D": "Paskal qonuni"}, "A", "pV = const - Boyl-Mariott"),
    ("Fizika", "Elektr va magnetizm", "Om qonunining zanjir bo'lagi uchun formulasi qaysi?", {"A": "I = U / R", "B": "U = I / R", "C": "R = U * I", "D": "P = I * U"}, "A", "I = U / R"),

    # Informatika
    ("Informatika", "Dasturlash", "Python tilida ekranga chiqarish funksiyasi qaysi?", {"A": "print()", "B": "console.log()", "C": "cout <<", "D": "System.out.println()"}, "A", "Python'da print() ishlatiladi"),
    ("Informatika", "Dasturlash", "Python'da ro'yxat yaratish sintaksisi qaysi?", {"A": "[1, 2, 3]", "B": "{1, 2, 3}", "C": "(1, 2, 3)", "D": "<1, 2, 3>"}, "A", "[ ] kvadrat qavslar ishlatiladi"),
    ("Informatika", "Axborot nazariyasi", "1 Bayt necha Bitga teng?", {"A": "8 Bit", "B": "10 Bit", "C": "1024 Bit", "D": "16 Bit"}, "A", "1 Bayt = 8 Bit"),
    ("Informatika", "Kompyuter tarmoqlari", "IP adres nechta oktetdan tashkil topgan?", {"A": "4 ta", "B": "8 ta", "C": "2 ta", "D": "6 ta"}, "A", "IPv4 4 ta oktetdan iborat"),

    # Ingliz tili
    ("Ingliz tili", "Grammar", "She ___ to school every day.", {"A": "goes", "B": "go", "C": "going", "D": "went"}, "A", "Present Simple, 3rd person singular - goes"),
    ("Ingliz tili", "Grammar", "They ___ a new car last week.", {"A": "bought", "B": "buy", "C": "buys", "D": "buying"}, "A", "Past Simple - bought"),
    ("Ingliz tili", "Vocabulary", "What is the synonym of 'happy'?", {"A": "Joyful", "B": "Sad", "C": "Angry", "D": "Tired"}, "A", "Happy = Joyful"),

    # Tarix
    ("Tarix", "O'zbekiston tarixi", "Amir Temur nechanchi yilda tug'ilgan?", {"A": "1336-yil", "B": "1405-yil", "C": "1236-yil", "D": "1370-yil"}, "A", "Amir Temur 1336-yil 9-aprelda tug'ilgan"),
    ("Tarix", "O'zbekiston tarixi", "Jaloliddin Manguberdi qaysi sulolaga mansub edi?", {"A": "Xorazmshohlar", "B": "Temuriylar", "C": "Qoraxoniylar", "D": "Shayboniylar"}, "A", "Xorazmshohlar sulolasi"),

    # Biologiya
    ("Biologiya", "Botanika", "Osimliklarda fotosintez jarayoni qaysi organda kechadi?", {"A": "Barg", "B": "Ildiz", "C": "Poya", "D": "Gullar"}, "A", "Fotosintez bargdagi xloroplastlarda kechadi"),
    ("Biologiya", "Zoologiya", "Sudralib yuruvchilarning yuragi necha kamerali?", {"A": "3 kamerali", "B": "2 kamerali", "C": "4 kamerali", "D": "1 kamerali"}, "A", "3 kamerali (timsohlarda 4)"),
]

INTRO_QUESTIONS_DATA = [
    ("Mantiqiy ketma-ketlikni davom ettiring: 2, 4, 8, 16, ...", {"A": "32", "B": "24", "C": "20", "D": "64"}, "A", " Har bir son 2 ga ko'paytirib boriladi", "logic"),
    ("To'g'ri to'rtburchakning eni 4 sm, bo'yi 6 sm. Yuzini toping.", {"A": "24 sm²", "B": "20 sm²", "C": "10 sm²", "D": "12 sm²"}, "A", "Yuzi S = a * b = 4 * 6 = 24 sm²", "logic"),
    ("Agar barcha mushuklar hayvon bo'lsa va Tom mushuk bo'lsa, Tom kim?", {"A": "Hayvon", "B": "Qush", "C": "Baliq", "D": "Osimlik"}, "A", "Sillogizm: Tom - hayvon", "logic"),
    ("Yangi fan yoki mavzuni o'rganishda sizga qaysi usul eng ko'p yordam beradi?", {"A": "Vizual grafiklar va misollar", "B": "Nazariy matnlarni mutolaa qilish", "C": "Amaliy mashqlar va testlar", "D": "Boshqalar bilan muhokama qilish"}, "A", "Shaxsiy ta'lim uslubini aniqlash", "psychology"),
]

class Command(BaseCommand):
    help = "Bazada 100 ta namunaviy savollarni va kirish savollarini yaratadi."

    def handle(self, *args, **options):
        self.stdout.write("Savollarni generatsiya qilish boshlandi...")

        created_count = 0

        # Create Subject -> Grade -> Topic -> Questions
        for subj_name, topic_name, text_base, options_base, correct_opt, explanation in SAMPLE_QUESTIONS_DATA:
            subject, _ = Subject.objects.get_or_create(name=subj_name)
            grade, _ = Grade.objects.get_or_create(subject=subject, name="Umumiy")
            topic, _ = Topic.objects.get_or_create(grade=grade, subject=subject, name=topic_name)

            # Generate 5-6 variations of each base question to reach 100+
            for i in range(1, 6):
                q_text = f"{text_base} (Variant #{i})" if i > 1 else text_base
                
                # Shuffle or adapt options
                opt_copy = dict(options_base)
                if i > 1:
                    opt_copy["A"] = f"{options_base['A']} [v{i}]"
                    opt_copy["B"] = f"{options_base['B']} [v{i}]"
                
                Question.objects.create(
                    topic=topic,
                    text=q_text,
                    options=opt_copy,
                    correct_option=correct_opt,
                    difficulty=random.randint(1, 5),
                    explanation=explanation,
                    status=Question.Status.PUBLISHED,
                    is_active=True,
                )
                created_count += 1

        # Recount questions for all topics
        for topic in Topic.objects.all():
            topic.recount_questions()

        # Intro questions
        intro_created = 0
        for text, opts, correct, expl, kind in INTRO_QUESTIONS_DATA:
            IntroQuestion.objects.get_or_create(
                text=text,
                defaults={
                    'options': opts,
                    'correct_option': correct,
                    'explanation': expl,
                    'kind': kind,
                    'is_active': True,
                }
            )
            intro_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Muvaffaqiyatli! Jami {created_count} ta bazaga test savollari va {intro_created} ta kirish testi savollari yaratildi."
        ))
