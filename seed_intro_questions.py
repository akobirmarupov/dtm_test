import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from intro.models import IntroQuestion

questions_data = [
    # Logic Questions (1 - 75)
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Mantiqiy ketma-ketlikni davom ettiring: 2, 4, 8, 16, ...",
        "options": {"A": "32", "B": "24", "C": "64", "D": "30"},
        "correct_option": "A",
        "explanation": "Har bir son oldingisidan 2 barobar katta (x2). 16 * 2 = 32."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "To'g'ri to'rtburchakning eni 4 sm, bo'yi 6 sm. Yuzini toping.",
        "options": {"A": "24 sm²", "B": "20 sm²", "C": "10 sm²", "D": "16 sm²"},
        "correct_option": "A",
        "explanation": "To'g'ri to'rtburchak yuzi S = a * b = 4 * 6 = 24 sm²."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Agar barcha mushuklar hayvon bo'lsa va Tom mushuk bo'lsa, Tom kim?",
        "options": {"A": "Hayvon", "B": "O'simlik", "C": "Qush", "D": "Inson"},
        "correct_option": "A",
        "explanation": "Mantiqiy sillogizm: Barcha mushuklar hayvon, Tom mushuk, demak Tom hayvon."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlikdagi keyingi kvadrat sonni toping: 1, 4, 9, 16, 25, ...",
        "options": {"A": "36", "B": "30", "C": "49", "D": "32"},
        "correct_option": "A",
        "explanation": "Sonlar kvadratlari: 1², 2², 3², 4², 5², 6² = 36."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 3, 6, 12, 24, ... keyingi son?",
        "options": {"A": "48", "B": "36", "C": "40", "D": "50"},
        "correct_option": "A",
        "explanation": "Har bir son 2 ga ko'paytirilmoqda: 24 * 2 = 48."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 100, 90, 80, 70, ... keyingi son?",
        "options": {"A": "60", "B": "50", "C": "65", "D": "55"},
        "correct_option": "A",
        "explanation": "Har safar 10 kamaymoqda: 70 - 10 = 60."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Soat 3:00 da soat va minut millari orasidagi burchak necha daraja?",
        "options": {"A": "90°", "B": "180°", "C": "45°", "D": "60°"},
        "correct_option": "A",
        "explanation": "Soat milli 3 da, minut milli 12 da bo'lganda tik (90°) burchak hosil bo'ladi."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Poyezd 60 km/h tezlikda 2 soat yurdi. Bosib o'tilgan masofani toping.",
        "options": {"A": "120 km", "B": "100 km", "C": "90 km", "D": "150 km"},
        "correct_option": "A",
        "explanation": "Masofa S = v * t = 60 * 2 = 120 km."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Teng yonli uchburchakning ikkita burchagi 50° va 50°. Uchinchi burchagini toping.",
        "options": {"A": "80°", "B": "100°", "C": "60°", "D": "90°"},
        "correct_option": "A",
        "explanation": "Uchburchak burchaklari yig'indisi 180°: 180° - 50° - 50° = 80°."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 5, 10, 15, 20, ... keyingi son?",
        "options": {"A": "25", "B": "30", "C": "22", "D": "24"},
        "correct_option": "A",
        "explanation": "Har safar 5 qo'shilmoqda: 20 + 5 = 25."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Agar 5 ta ishchi 5 soatda 5 ta detal yasasa, 100 ta ishchi 100 ta detalni necha soatda yasaydi?",
        "options": {"A": "5 soatda", "B": "100 soatda", "C": "20 soatda", "D": "1 soatda"},
        "correct_option": "A",
        "explanation": "Har bir ishchi 1 ta detalni 5 soatda yasaydi. Demak 100 ta ishchi ham 100 ta detalni 5 soatda yasaydi."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "1 dan 10 gacha bo'lgan barcha butun sonlar yig'indisi nechaga teng?",
        "options": {"A": "55", "B": "50", "C": "45", "D": "60"},
        "correct_option": "A",
        "explanation": "1+2+3+4+5+6+7+8+9+10 = 55 (yoki (1+10)*10/2 = 55)."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Sonni 0.5 ga bo'lish nima bilan teng?",
        "options": {"A": "2 ga ko'paytirishga", "B": "2 ga bo'lishga", "C": "O'zgarishsiz qolishiga", "D": "0.5 ni ayirishga"},
        "correct_option": "A",
        "explanation": "x / 0.5 = x / (1/2) = x * 2."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 2, 3, 5, 7, 11, 13, ... keyingi tub son qaysi?",
        "options": {"A": "17", "B": "15", "C": "19", "D": "14"},
        "correct_option": "A",
        "explanation": "Tub sonlar ketma-ketligi: 13 dan keyingi tub son 17."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Mashina 100 km masofaga 8 litr yonilg'i sarflaydi. 300 km ga qancha sarflaydi?",
        "options": {"A": "24 litr", "B": "16 litr", "C": "32 litr", "D": "20 litr"},
        "correct_option": "A",
        "explanation": "300 km = 3 * 100 km. Sarf: 3 * 8 = 24 litr."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "'Kitob' so'ziga 'Muallif' mos kelsa, 'Rasm' so'ziga kim mos keladi?",
        "options": {"A": "Rassom", "B": "Shoir", "C": "Haykaltarosh", "D": "Kompozitor"},
        "correct_option": "A",
        "explanation": "Kitobni muallif yozadi, rasmni rassom chizadi."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Qaysi figura shakli bo'yicha qolganlaridan tubdan farq qiladi?",
        "options": {"A": "Doira", "B": "Kvadrat", "C": "Uchburchak", "D": "To'rtburchak"},
        "correct_option": "A",
        "explanation": "Doira burchak va to'g'ri tomonlarga ega emas."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Sonning 25% qismi 15 ga teng bo'lsa, sonning o'zi nechaga teng?",
        "options": {"A": "60", "B": "45", "C": "75", "D": "50"},
        "correct_option": "A",
        "explanation": "25% = 1/4 qismi. Son = 15 * 4 = 60."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 1, 1, 2, 3, 5, 8, 13, ... keyingi Fibonachchi soni?",
        "options": {"A": "21", "B": "20", "C": "19", "D": "25"},
        "correct_option": "A",
        "explanation": "Har bir son oxirgi ikkitasining yig'indisi: 8 + 13 = 21."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Kubning nechta yoqlari (tomonlari) bor?",
        "options": {"A": "6 ta", "B": "8 ta", "C": "12 ta", "D": "4 ta"},
        "correct_option": "A",
        "explanation": "Kub 6 ta teng kvadrat yoqqa ega."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "30 ning 10% ini toping.",
        "options": {"A": "3", "B": "30", "C": "0.3", "D": "6"},
        "correct_option": "A",
        "explanation": "30 * 10 / 100 = 3."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 81, 27, 9, 3, ... keyingi son?",
        "options": {"A": "1", "B": "0", "C": "1/3", "D": "2"},
        "correct_option": "A",
        "explanation": "Har safar 3 ga bo'linmoqda: 3 / 3 = 1."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Akasi ukasidan 4 yosh katta. 5 yildan keyin yoshlar orasidagi farq qancha bo'ladi?",
        "options": {"A": "4 yosh", "B": "9 yosh", "C": "1 yosh", "D": "5 yosh"},
        "correct_option": "A",
        "explanation": "Yoshlar orasidagi farq vaqt o'tishi bilan o'zgarmaydi (4 yosh)."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Qaysi oyda 28 kun bor?",
        "options": {"A": "Barcha oylarda", "B": "Faqat fevralda", "C": "Yanvarda", "D": "Martda"},
        "correct_option": "A",
        "explanation": "Barcha oylarda kamida 28 kun bor."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 2, 6, 12, 20, 30, ... keyingi son?",
        "options": {"A": "42", "B": "36", "C": "40", "D": "50"},
        "correct_option": "A",
        "explanation": "Farqlar: +4, +6, +8, +10, +12. 30 + 12 = 42 (yoki n*(n+1): 6*7=42)."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Kvadratning perimetri 36 sm bo'lsa, uning bir tomoni necha sm?",
        "options": {"A": "9 sm", "B": "6 sm", "C": "12 sm", "D": "18 sm"},
        "correct_option": "A",
        "explanation": "P = 4 * a => a = 36 / 4 = 9 sm."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Qaysi so'z mantiqan ortiqcha: Olma, Nok, Shaftoli, Sabzi?",
        "options": {"A": "Sabzi", "B": "Olma", "C": "Nok", "D": "Shaftoli"},
        "correct_option": "A",
        "explanation": "Sabzi - sabzavot, qolganlari mevalar."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "2 ning 5-darajasi nechaga teng?",
        "options": {"A": "32", "B": "10", "C": "25", "D": "64"},
        "correct_option": "A",
        "explanation": "2 * 2 * 2 * 2 * 2 = 32."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Uchburchakning ichki burchaklari yig'indisi necha daraja?",
        "options": {"A": "180°", "B": "360°", "C": "90°", "D": "270°"},
        "correct_option": "A",
        "explanation": "Hamma tekis uchburchaklarning ichki burchaklari yig'indisi 180°."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 7, 14, 21, 28, ... keyingi son?",
        "options": {"A": "35", "B": "32", "C": "42", "D": "36"},
        "correct_option": "A",
        "explanation": "7 ga karrali sonlar: 28 + 7 = 35."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Bir sutkada necha minut bor?",
        "options": {"A": "1440 minut", "B": "1200 minut", "C": "3600 minut", "D": "864 minut"},
        "correct_option": "A",
        "explanation": "24 soat * 60 minut = 1440 minut."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Qaysi amal birinchi bajariladi: 2 + 3 * 4?",
        "options": {"A": "Ko'paytirish (3 * 4)", "B": "Qo'shish (2 + 3)", "C": "Chapdan o'ngga", "D": "Ixtiyoriy"},
        "correct_option": "A",
        "explanation": "Matematika qoidalariga ko'ra ko'paytirish qo'shishdan oldin bajariladi."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 100, 50, 25, ... keyingi son?",
        "options": {"A": "12.5", "B": "10", "C": "15", "D": "5"},
        "correct_option": "A",
        "explanation": "Har safar 2 ga bo'linmoqda: 25 / 2 = 12.5."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Doiraning radiusi 5 sm bo'lsa, diametri necha sm?",
        "options": {"A": "10 sm", "B": "25 sm", "C": "15 sm", "D": "20 sm"},
        "correct_option": "A",
        "explanation": "Diametr d = 2 * r = 2 * 5 = 10 sm."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Qaysi so'z mantiqan mos emas: Samolyot, Vertolyot, Kosmik kema, Avtobus?",
        "options": {"A": "Avtobus", "B": "Samolyot", "C": "Vertolyot", "D": "Kosmik kema"},
        "correct_option": "A",
        "explanation": "Avtobus yer usti transporti, qolganlari havo/fazoviy transport."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 4, 9, 16, 25, 36, ... keyingi kvadrat son?",
        "options": {"A": "49", "B": "64", "C": "40", "D": "45"},
        "correct_option": "A",
        "explanation": "7² = 49."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Qaysi metall xona haroratida suyuq holda bo'ladi?",
        "options": {"A": "Simob", "B": "Oltin", "C": "Temir", "D": "Mis"},
        "correct_option": "A",
        "explanation": "Simob (Hg) normal sharoitda suyuq bo'lgan yagona metall."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Qaysi oyda kun va tun tenglashishi (bahoriy tenglik) yuz beradi?",
        "options": {"A": "Mart", "B": "Iyun", "C": "Yanvar", "D": "Avgust"},
        "correct_option": "A",
        "explanation": "21-mart kuni bahoriy teng kunlik yuz beradi."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 1, 8, 27, 64, ... keyingi kubik son?",
        "options": {"A": "125", "B": "100", "C": "216", "D": "81"},
        "correct_option": "A",
        "explanation": "5³ = 125."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Yilning nechanchi oyi Avgust hisoblanadi?",
        "options": {"A": "8-oyi", "B": "7-oyi", "C": "9-oyi", "D": "6-oyi"},
        "correct_option": "A",
        "explanation": "Avgust - yilning 8-oyi."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Otasining yoshi 40 da, o'g'liniki 10 da. Necha yildan keyin o'g'il otasidan 2 barobar kichik bo'ladi?",
        "options": {"A": "20 yildan keyin", "B": "10 yildan keyin", "C": "15 yildan keyin", "D": "30 yildan keyin"},
        "correct_option": "A",
        "explanation": "20 yildan keyin ota 60, o'g'il 30 yoshda bo'ladi (60 / 30 = 2)."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "0.75 kasr foizda qanday yoziladi?",
        "options": {"A": "75%", "B": "7.5%", "C": "0.75%", "D": "750%"},
        "correct_option": "A",
        "explanation": "0.75 * 100% = 75%."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: A, C, E, G, ... keyingi harf?",
        "options": {"A": "I", "B": "H", "C": "J", "D": "K"},
        "correct_option": "A",
        "explanation": "Lotin alifbosida bittadan o'tkazib: A(1), C(3), E(5), G(7), I(9)."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Kvadratning yuzi 64 sm² bo'lsa, perimetri qancha?",
        "options": {"A": "32 sm", "B": "16 sm", "C": "64 sm", "D": "24 sm"},
        "correct_option": "A",
        "explanation": "a = √64 = 8 sm. Perimetr P = 4 * 8 = 32 sm."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Qaysi organ inson tanasida qonni haydaydi?",
        "options": {"A": "Yurak", "B": "Jigar", "C": "O'pka", "D": "Buyrak"},
        "correct_option": "A",
        "explanation": "Yurak qon tomir tizimida nasos vazifasini bajaradi."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 2, 5, 10, 17, 26, ... keyingi son?",
        "options": {"A": "37", "B": "35", "C": "40", "D": "32"},
        "correct_option": "A",
        "explanation": "Formula: n² + 1. 6² + 1 = 37."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Bir kilogramm paxta og'irmi yoki bir kilogramm temir?",
        "options": {"A": "Ikkalasi teng", "B": "Temir og'ir", "C": "Paxta og'ir", "D": "Taqqoslab bo'lmaydi"},
        "correct_option": "A",
        "explanation": "Ikkalasi ham 1 kg, demak massalari teng."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 64, 32, 16, 8, ... keyingi son?",
        "options": {"A": "4", "B": "2", "C": "6", "D": "0"},
        "correct_option": "A",
        "explanation": "8 / 2 = 4."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "15 ning kvadratini toping.",
        "options": {"A": "225", "B": "150", "C": "200", "D": "250"},
        "correct_option": "A",
        "explanation": "15 * 15 = 225."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Suv necha daraja Selsiyda qaynaydi (normal atmosferada)?",
        "options": {"A": "100°C", "B": "90°C", "C": "120°C", "D": "80°C"},
        "correct_option": "A",
        "explanation": "Normal bosimda suvning qaynash harorati 100°C."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Tenglama yechimi: 2x + 6 = 14. x ni toping.",
        "options": {"A": "4", "B": "3", "C": "5", "D": "6"},
        "correct_option": "A",
        "explanation": "2x = 8 => x = 4."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 3, 7, 11, 15, ... keyingi son?",
        "options": {"A": "19", "B": "18", "C": "21", "D": "17"},
        "correct_option": "A",
        "explanation": "Har safar +4 qo'shilmoqda: 15 + 4 = 19."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "O'zbekiston Respublikasi poytaxti qaysi shahar?",
        "options": {"A": "Toshkent", "B": "Samarqand", "C": "Buxoro", "D": "Namangan"},
        "correct_option": "A",
        "explanation": "Toshkent - O'zbekiston poytaxti."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Qaysi fasl Yerdagi shimoliy yarim sharda dekabr oyida bo'ladi?",
        "options": {"A": "Qish", "B": "Yoz", "C": "Kuz", "D": "Bahor"},
        "correct_option": "A",
        "explanation": "Dekabr shimoliy yarim sharda qish oyi hisoblanadi."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 1, 3, 6, 10, 15, ... keyingi uchburchak son?",
        "options": {"A": "21", "B": "20", "C": "18", "D": "25"},
        "correct_option": "A",
        "explanation": "+2, +3, +4, +5, +6. 15 + 6 = 21."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "100 ning 0% i nechaga teng?",
        "options": {"A": "0", "B": "100", "C": "1", "D": "10"},
        "correct_option": "A",
        "explanation": "Har qanday sonning 0 foizi 0 ga teng."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Inson miyasining necha foizga yaqin qismi suvdan iborat?",
        "options": {"A": "~75-80%", "B": "~20%", "C": "~50%", "D": "~95%"},
        "correct_option": "A",
        "explanation": "Inson miyasi taxminan 75-80% suvdan tashkil topgan."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: Z, Y, X, W, ... keyingi harf?",
        "options": {"A": "V", "B": "U", "C": "T", "D": "S"},
        "correct_option": "A",
        "explanation": "Lotin alifbosi teskari tartibda: W dan oldingi harf V."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "12 va 18 sonlarining eng katta umumiy bo'luvchisi (EKUB) nechaga teng?",
        "options": {"A": "6", "B": "3", "C": "12", "D": "36"},
        "correct_option": "A",
        "explanation": "12 va 18 sonlarining ikkalasi ham bo'linadigan eng katta son 6."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 4, 8, 12, 16, ... keyingi son?",
        "options": {"A": "20", "B": "24", "C": "18", "D": "22"},
        "correct_option": "A",
        "explanation": "Har safar +4 qo'shilmoqda: 16 + 4 = 20."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Uchburchakning asosi a=8 sm, balandligi h=5 sm. Yuzini toping.",
        "options": {"A": "20 sm²", "B": "40 sm²", "C": "13 sm²", "D": "30 sm²"},
        "correct_option": "A",
        "explanation": "S = (a * h) / 2 = (8 * 5) / 2 = 20 sm²."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Dunyodagi eng katta okean qaysi?",
        "options": {"A": "Tinch okeani", "B": "Atlantika okeani", "C": "Hind okeani", "D": "Shimoliy muz okeani"},
        "correct_option": "A",
        "explanation": "Tinch okeani (Tinch okeani) Yerdagi eng katta okeandir."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 9, 18, 27, 36, ... keyingi son?",
        "options": {"A": "45", "B": "40", "C": "54", "D": "42"},
        "correct_option": "A",
        "explanation": "36 + 9 = 45."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Bir yilda necha hafta bor?",
        "options": {"A": "52 hafta", "B": "48 hafta", "C": "60 hafta", "D": "50 hafta"},
        "correct_option": "A",
        "explanation": "365 / 7 = 52.14, ya'ni taxminan 52 to'liq hafta."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "5! (5 faktorial) nechaga teng?",
        "options": {"A": "120", "B": "60", "C": "100", "D": "24"},
        "correct_option": "A",
        "explanation": "1 * 2 * 3 * 4 * 5 = 120."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 10, 20, 40, 80, ... keyingi son?",
        "options": {"A": "160", "B": "100", "C": "120", "D": "200"},
        "correct_option": "A",
        "explanation": "80 * 2 = 160."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Quyosh tizimidagi eng katta planeta qaysi?",
        "options": {"A": "Yupiter", "B": "Mars", "C": "Saturn", "D": "Yer"},
        "correct_option": "A",
        "explanation": "Yupiter - Quyosh tizimidagi eng ulkan planeta."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 50, 45, 40, 35, ... keyingi son?",
        "options": {"A": "30", "B": "25", "C": "32", "D": "28"},
        "correct_option": "A",
        "explanation": "Har safar -5 kamaymoqda: 35 - 5 = 30."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "To'rtburchakning ichki burchaklari yig'indisi necha daraja?",
        "options": {"A": "360°", "B": "180°", "C": "540°", "D": "270°"},
        "correct_option": "A",
        "explanation": "Hamma qavariq to'rtburchaklar ichki burchaklari yig'indisi 360°."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 2, 4, 7, 11, 16, ... keyingi son?",
        "options": {"A": "22", "B": "20", "C": "21", "D": "23"},
        "correct_option": "A",
        "explanation": "Ketma-ket farqlar: +2, +3, +4, +5, +6. 16 + 6 = 22."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "3 ning 4-darajasi nechaga teng?",
        "options": {"A": "81", "B": "27", "C": "64", "D": "12"},
        "correct_option": "A",
        "explanation": "3 * 3 * 3 * 3 = 81."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Kompyuter xotirasida 1 Kilobayt necha baytga teng?",
        "options": {"A": "1024 bayt", "B": "1000 bayt", "C": "512 bayt", "D": "2048 bayt"},
        "correct_option": "A",
        "explanation": "Binary xotira o'lchamida 1 KB = 2^10 = 1024 bayt."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 11, 22, 33, 44, ... keyingi son?",
        "options": {"A": "55", "B": "66", "C": "50", "D": "45"},
        "correct_option": "A",
        "explanation": "44 + 11 = 55."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Qaysi elementning kimyoviy belgisi 'O' hisoblanadi?",
        "options": {"A": "Kislorod (Oxygen)", "B": "Oltin", "C": "Azot", "D": "Vodorod"},
        "correct_option": "A",
        "explanation": "'O' - Kislorod (Oxygen) elementining kimyoviy belgisi."
    },
    {
        "kind": IntroQuestion.Kind.LOGIC,
        "text": "Ketma-ketlik: 100, 81, 64, 49, ... keyingi kvadrat son?",
        "options": {"A": "36", "B": "25", "C": "30", "D": "40"},
        "correct_option": "A",
        "explanation": "10², 9², 8², 7², 6² = 36."
    },

    # Psychology Questions (76 - 100)
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Yangi fan yoki mavzuni o'rganishda sizga qaysi usul eng ko'p yordam beradi?",
        "options": {
            "A": "Amaliy mashqlar va testlar yechish",
            "B": "Kitob va konspektlarni sinchiklab o'qish",
            "C": "Videodarsliklar va ko'rgazmali vositalar",
            "D": "Boshqalar bilan muhokama qilish"
        },
        "correct_option": "",
        "explanation": "Psixologik savol: Har bir insonning o'z o me'yoridagi o'rganish uslubi (vaziyatga ko'ra) mavjud."
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Qiyin masalaga duch kelganingizda birinchi harakatingiz qanday bo'ladi?",
        "options": {
            "A": "O'zim mustaqil yechim izlayman",
            "B": "Ustoz yoki do'stlarimdan yordam so'rayman",
            "C": "Internet va sun'iy intellektdan qidiraman",
            "D": "Biroz tanaffus qilib keyin qaytaman"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Dars tayyorlash uchun qaysi vaqt siz uchun eng samarali?",
        "options": {
            "A": "Ertalab barvaqt",
            "B": "Tushdan keyin",
            "C": "Kechqurun",
            "D": "Tungi vaqtda"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Imtihonga tayyorgarlik ko'rishda qaysi reja sizga mos keladi?",
        "options": {
            "A": "Har kuni oz-ozdan tartibli o'rganish",
            "B": "Oxirgi haftada intensiv tayyorlanish",
            "C": "Faqat qiyin mavzularga urg'u berish",
            "D": "Testlar orqali bilimni sinab borish"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "O'zingizni qaysi yo'nalishda kuchliroq deb hisoblaysiz?",
        "options": {
            "A": "Aniq va tabiiy fanlar (Matematika, Fizika)",
            "B": "Gumanitar fanlar (Tarix, Adabiyot)",
            "C": "Xorijiy tillar va muloqot",
            "D": "AT va dasturlash"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Xato qilganingizda munosabatingiz qanday bo'ladi?",
        "options": {
            "A": "Xatoni tahlil qilib to'g'rilayman",
            "B": "Tushkunlikka tushaman lekin davom etaman",
            "C": "Yangi usul sinab ko'raman",
            "D": "Masalani chetga surib qo'yaman"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Dars jarayonida diqqatingizni jamlashga nima eng ko'p yordam beradi?",
        "options": {
            "A": "Tinch va jimjit muhit",
            "B": "Yoqimli fon musiqasi",
            "C": "Aniq belgilangan tanaffuslar",
            "D": "Maqsad va taymer qo'yish"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Kelajakdagi kasbingizni tanlashda qaysi omil eng muhim?",
        "options": {
            "A": "Qiziqish va yoqtirgan mashg'ulot",
            "B": "Yuqori daromad va imkoniyatlar",
            "C": "Jamiyatga foyda keltirish",
            "D": "Karyera va o'sish"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Ma'lumotni eslab qolishning eng ma'qul usuli siz uchun qaysi?",
        "options": {
            "A": "Qayta-qayta yozib olish va konspekt qilish",
            "B": "O'z so'zlarim bilan aytib berish",
            "C": "Chizma va sxemalar chizish",
            "D": "Amalda qo'llab ko'rish"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Bir vaqtning o'zida bir nechta vazifa berilsa qanday yo'l tutasiz?",
        "options": {
            "A": "Eng muhimidan boshlab tartib bilan bajaraman",
            "B": "Eng osonidan boshlayman",
            "C": "Hamma vazifani parallel olib boraman",
            "D": "Reja tuzib keyin kirishaman"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Jamoaviy loyihada qaysi rolni afzal ko'rasiz?",
        "options": {
            "A": "Lider va tashkilotchi",
            "B": "G'oya beruvchi va kreativ fikrlovchi",
            "C": "Ijrochi va puxta bajaruvchi",
            "D": "Tahlilchi va tekshiruvchi"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Muvaffaqiyatga erishish uchun eng muhim sifat qaysi?",
        "options": {
            "A": "Mehnatkashlik va tirishqoqlik",
            "B": "Iste'dod va mantiq",
            "C": "To'g'ri rejalashtirish va intizom",
            "D": "O'ziga bo'lgan ishonch"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Stressli holatda (masalan, imtihon oldidan) o'zingizni qanday tinchlantirasiz?",
        "options": {
            "A": "Chuqur nafas olib o'zimga ishonch bag'ishlayman",
            "B": "Musiqa eshitaman yoki sayr qilaman",
            "C": "Barcha bilimlarimni qayta ko'rib chiqaman",
            "D": "Do'stlarim bilan suhbatlashaman"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Onlayn ta'limning qaysi afzalligi sizga eng yoqadi?",
        "options": {
            "A": "O'z vaqtim va sur'atimda o'rganish",
            "B": "Istalgan joydan darslarga kirish",
            "C": "Qayta ko'rish imkoniyati",
            "D": "Boy ko'rgazmali va interaktiv materiallar"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Maqsadingizga erishishda sizni eng ko'p nima ruhlantiradi?",
        "options": {
            "A": "Natijaga erishish va g'alaba tuyg'usi",
            "B": "Ota-ona va yaqinlar xursandchiligi",
            "C": "Yangi bilimlarni egallash",
            "D": "Tan olinish va muvaffaqiyat"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Qaysi turdagi topshiriqlar sizga ko'proq yoqadi?",
        "options": {
            "A": "Mantiqiy va analitik topshiriqlar",
            "B": "Ijodiy va erkin topshiriqlar",
            "C": "Amaliy va hayotiy vaziyatlar",
            "D": "Xotira va faktlarga asoslangan"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Kuningizni qanday rejalashtirasiz?",
        "options": {
            "A": "Aniq kun tartibi va vazifalar ro'yxati tuzaman",
            "B": "Asosiy 2-3 ta vazifani belgilayman",
            "C": "Vaziyatga qarab moslashaman",
            "D": "Rejasiz, erkin harakat qilaman"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Yangi dastur yoki vositani o'rganishda qanday yo'l tutasiz?",
        "options": {
            "A": "Darhol ishlatib ko'rib o'rganaman",
            "B": "Yo'riqnoma va qo'llanmani o'qiyman",
            "C": "Video darsliklarni tomosha qilaman",
            "D": "Tajribali insonlardan so'rayman"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "O'rinli tanqidga qanday munosabat bildirasiz?",
        "options": {
            "A": "Xatolardan xulosa chiqarib rivojlanaman",
            "B": "E'tibor beraman lekin o'zimga yaqin olmayman",
            "C": "O'zimni oqlashga harakat qilaman",
            "D": "Xafa bo'laman"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Vaqtni boshqarishda (Time management) qaysi muammoga tez-tez duch kelasiz?",
        "options": {
            "A": "Ishlarni oxirgi daqiqaga surish (prokrastinatsiya)",
            "B": "Diqqatning bo'linishi (ijtimoiy tarmoqlar)",
            "C": "Rejadagi topshiriqlarning ko'pligi",
            "D": "Hech qanday muammo yo'q, vaqtim yetarli"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Kitob o'qishda nimaga ko'proq e'tibor berasiz?",
        "options": {
            "A": "Asosiy g'oya va mantiqiy xulosalarga",
            "B": "Muallifning uslubi va tuyg'ulariga",
            "C": "Amaliy maslahatlarga",
            "D": "Qiziqarli voqealar rivojiga"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "O'quv maqsadlaringizni qanchalik tez-tez qayta ko'rib chiqasiz?",
        "options": {
            "A": "Har oyda bir marta",
            "B": "Har haftada bir marta",
            "C": "Yilda bir marta",
            "D": "Faqat zarurat tug'ilganda"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Qaysi bilimni egallashni hozirgi kunda eng muhim deb bilasiz?",
        "options": {
            "A": "Sun'iy intellekt va zamonaviy texnologiyalar",
            "B": "Moliya va biznes savodxonligi",
            "C": "Chet tillari va muloqot",
            "D": "Psixologiya va shaxsiy rivojlanish"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "O'quv materialini o'zlashtirishda eng yaxshi baholash usuli qaysi?",
        "options": {
            "A": "Test savollari",
            "B": "Yozma insho yoki esse",
            "C": "Amaliy loyiha va taqdimot",
            "D": "Og'zaki imtihon"
        },
        "correct_option": "",
        "explanation": ""
    },
    {
        "kind": IntroQuestion.Kind.PSYCHOLOGY,
        "text": "Antigravity/Univora platformasidan asosiy kutayotgan natijangiz nima?",
        "options": {
            "A": "Yuqori ball to'plab OTMga kirish",
            "B": "Mantiqiy va analitik fikrlashni rivojlantirish",
            "C": "Fanlarni chuqur va oson o'rganish",
            "D": "O'z bilim va darajamni doimiy baholash"
        },
        "correct_option": "",
        "explanation": ""
    }
]

def seed():
    print(f"Starting seed of {len(questions_data)} intro questions...")
    # Clear existing if needed, or add missing
    existing_count = IntroQuestion.objects.count()
    print(f"Existing count in DB: {existing_count}")

    created_count = 0
    for idx, item in enumerate(questions_data, start=1):
        obj, created = IntroQuestion.objects.get_or_create(
            text=item["text"],
            defaults={
                "kind": item["kind"],
                "options": item["options"],
                "correct_option": item["correct_option"],
                "explanation": item.get("explanation", ""),
                "order": idx,
                "is_active": True
            }
        )
        if created:
            created_count += 1

    total_now = IntroQuestion.objects.count()
    print(f"Seeding finished. Created {created_count} new questions. Total count in DB: {total_now}")

if __name__ == '__main__':
    seed()
