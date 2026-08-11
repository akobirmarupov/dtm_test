# 🎨 FIGMA UI DESIGN GUIDE - DTM TEST PLATFORM

## OVERVIEW
Bu guide-da **DTM Test Platform**-ning barcha screens, buttons va flows tasvirlangan. Figma-da yasashda ushbu structure-ga amal qiling.

---

## 📱 SCREEN STRUCTURE

### COLOR PALETTE (RECOMMENDED)
```
Primary: #007AFF (Blue - Action buttons)
Secondary: #5AC8FA (Light Blue)
Success: #34C759 (Green - Correct answer)
Danger: #FF3B30 (Red - Wrong answer)
Warning: #FF9500 (Orange - Attention)
Background: #F5F5F5 (Light Gray)
Text Primary: #000000
Text Secondary: #666666
Border: #CCCCCC
```

### TYPOGRAPHY
```
Header 1: 28px Bold
Header 2: 22px Bold
Header 3: 18px Semibold
Body: 16px Regular
Small: 14px Regular
Tiny: 12px Regular
```

---

## 🔐 SCREEN 1: LOGIN / AUTHENTICATION

### Layout:
```
┌─────────────────────────┐
│                         │
│    📚 TESTYOURSELF      │ (Logo)
│                         │
│  Bosh sahifada test     │ (Subtitle - 16px)
│  yechib ketmonasini     │
│  o'zingizni sinab ko'ring│
│                         │
│  ┌─────────────────────┐│
│  │  [G] Google orqali  ││ (OAuth Button - 44px height)
│  │      Kirish         ││ Color: White, Border: #CCCCCC
│  └─────────────────────┘│
│                         │
│  Shartlar va Siyosat >  │ (Link - 14px)
│                         │
└─────────────────────────┘
```

### Button Actions:
- **Google Login Button**: `POST /api/auth/google/`
- Store tokens: `localStorage.setItem('access_token', response.access)`
- Redirect: → HOME SCREEN

### Code Implementation (Frontend):
```javascript
// React/Vue example
const handleGoogleLogin = async (idToken) => {
  const response = await fetch('/api/auth/google/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_token: idToken })
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('user', JSON.stringify(data.user));
  redirect('/home');
};
```

---

## 🏠 SCREEN 2: HOME / DASHBOARD

### Layout:
```
┌──────────────────────────────┐
│ ← | Testyourself | ☰         │ (Header - 56px)
├──────────────────────────────┤
│                              │
│  Xo'sh kelibsiz, ALI! 👋      │ (Greeting - 20px Bold)
│  Biz sizga mamnun 🎉          │
│                              │
├──────────────────────────────┤
│  📊 STATISTIKA                │ (Section Header)
├──────────────────────────────┤
│  ┌─────────────┐ ┌─────────┐ │
│  │ 💎           │ │ 🔥      │ │ (Cards - 2 columns)
│  │ XP: 1,250    │ │ 7 KUN   │ │
│  │              │ │ STREAK  │ │
│  └─────────────┘ └─────────┘ │
│                              │
│  ┌──────────────────────────┐ │
│  │ 💰 OBUNA: Premium Active  │ │ (Subscription card)
│  │ Muddati: 20 kun qolgan    │ │
│  │ [Yangilash]               │ │
│  └──────────────────────────┘ │
│                              │
├──────────────────────────────┤
│  🎯 ASOSIY TUGMALAR           │ (Action Buttons)
├──────────────────────────────┤
│                              │
│  ┌─────────────────────────┐ │
│  │ 📖 TEST YECHISH         │ │ (Full width button)
│  │ Yangi test yaratish     │ │ Height: 56px
│  │ Mode tanlang: Practice/ │ │ BG: #007AFF
│  │ Exam                    │ │ Text: White
│  └─────────────────────────┘ │
│                              │
│  ┌─────────────────────────┐ │
│  │ 📋 TAKRORLASH           │ │
│  │ 5 ta savol bugun        │ │
│  └─────────────────────────┘ │
│                              │
│  ┌─────────────────────────┐ │
│  │ 📊 NATIJALARIM          │ │
│  │ 15 ta test yakunlandi   │ │
│  └─────────────────────────┘ │
│                              │
│  ┌─────────────────────────┐ │
│  │ 🏆 LEADERBOARD          │ │
│  │ 1. Ali (500 XP)         │ │
│  │ 2. Vali (450 XP)        │ │
│  │ 3. Sohib (400 XP)       │ │
│  └─────────────────────────┘ │
│                              │
├──────────────────────────────┤
│ 🏠 Home | 👤 Profile | ⚙️ Set│ (Bottom Tab)
└──────────────────────────────┘
```

### API Calls:
```javascript
// Componentga o'tuvchi vaqtda:
GET /api/auth/me/                    // Profil
GET /progress/streak/                // Streak
GET /progress/xp/summary/            // XP
GET /billing/subscriptions/current/  // Obuna
GET /progress/reviews/today/         // Takrorlash soni
GET /testengine/results/my-results/  // Test natijalari
GET /progress/leaderboard/weekly/    // Leaderboard
```

### Button Actions:
| Button | Action | API |
|--------|--------|-----|
| Test Yechish | → Test Screening | POST /testengine/sessions/ |
| Takrorlash | → Review Screen | GET /progress/reviews/today/ |
| Natijalarim | → Results Screen | GET /testengine/results/my-results/ |
| Leaderboard | → Leaderboard Screen | GET /progress/leaderboard/weekly/ |

---

## 🎯 SCREEN 3: TEST MODE SELECTION

### Layout:
```
┌──────────────────────────────┐
│ < REJIM TANLASH              │ (Header)
├──────────────────────────────┤
│                              │
│  Qaysi rejimda test yechish  │ (Title - 18px)
│  ni istaysiz?                │
│                              │
│  ┌─────────────────────────┐ │
│  │  PRACTICE MODE          │ │ (Card - Selectable)
│  │  ═════════════════      │ │ Border width: 2px (selected)
│  │  ✓ Cheksiz vaqt        │ │ BG: #F5F5F5 (normal)
│  │  ✓ Fikr qash mumkin     │ │ BG: #E3F2FD (selected)
│  │  ✓ Qiyinligi o'rtacha   │ │
│  │  ✓ O'rganish uchun      │ │
│  │  [TANLASH]              │ │
│  └─────────────────────────┘ │
│                              │
│  ┌─────────────────────────┐ │
│  │  EXAM MODE (Premium)    │ │
│  │  ═════════════════      │ │
│  │  ⏱️ 30 minut vaqt       │ │
│  │  ❌ Fikr qash mumkin emas│ │
│  │  ❌ Orqaga qaytish mumkin│ │
│  │  💎 Imtihon uchun       │ │
│  │  [TANLASH] (grayed)     │ │
│  │  (Yoki Premium ol)      │ │
│  └─────────────────────────┘ │
│                              │
└──────────────────────────────┘
```

### Subject Selection Dialog:
```
┌─────────────────────────────┐
│ FAN TANLANG                  │ (Modal header)
├─────────────────────────────┤
│ 🔍 [Qidirish...]            │ (Search input)
├─────────────────────────────┤
│ ┌──────────┐ ┌──────────┐   │
│ │📐 Matema │ │🔬 Fizika │   │ (2x2 grid)
│ │tika      │ │          │   │
│ └──────────┘ └──────────┘   │
│                              │
│ ┌──────────┐ ┌──────────┐   │
│ │🧪 Kimyo  │ │📚 Biolo  │   │
│ │          │ │giya      │   │
│ └──────────┘ └──────────┘   │
│                              │
└─────────────────────────────┘
```

### API & Actions:
```javascript
// Fan tanlash
const handleSubjectSelect = (subjectId) => {
  fetch('/testengine/sessions/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      subject_id: subjectId,
      mode: selectedMode  // "practice" or "exam"
    })
  })
  .then(res => res.json())
  .then(data => {
    navigate(`/test/${data.id}`);  // Yangi screen ga o'tish
  });
};
```

---

## ❓ SCREEN 4: TEST SESSION (QUESTION ANSWERING)

### Layout:
```
┌──────────────────────────────────┐
│ < | Test 5/20 | ⏱️ 12:34        │ (Header - 56px)
│   Progress: ▓▓▓▓░░░░░░░░░░░░░░  │ (Progress bar)
├──────────────────────────────────┤
│                                  │
│  📖 SAVOL 5/20                   │ (Question number - 14px)
│                                  │
│  2 + 2 ning qiymati qanday?      │ (Question text - 18px Bold)
│                                  │
├──────────────────────────────────┤
│  VARIANTLAR:                      │ (Options section)
│                                  │
│  ┌──────────────────────────────┐ │
│  │ ◯ A) 3                       │ │ (Radio button - 48px)
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │ ◉ B) 4                       │ │ (Selected - filled circle)
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │ ◯ C) 5                       │ │
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │ ◯ D) 6                       │ │
│  └──────────────────────────────┘ │
│                                  │
├──────────────────────────────────┤
│  ISHONCH DARAJASI:                │
│                                  │
│  ┌──────────┐  ┌──────────┐      │
│  │◉ Ishonch │  │◯ Taxmin  │      │ (Radio group)
│  └──────────┘  └──────────┘      │
│                                  │
├──────────────────────────────────┤
│  ┌──────────────────────────────┐ │
│  │ KEYINGI >                    │ │ (Next button)
│  │ (yoki TUGATISH last question │ │
│  │ bo'lganda)                   │ │
│  └──────────────────────────────┘ │
│                                  │
└──────────────────────────────────┘
```

### Interactive Behavior:
```javascript
// Javob tanlash
const handleAnswerSelect = (option) => {
  setSelectedOption(option);
  // POST request SHUCHU send qilma, buttonni bosishini kut
};

// Keyingi
const handleNext = async () => {
  // 1. Javobni save qil
  await fetch(`/testengine/sessions/${sessionId}/answers/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      question_id: currentQuestion.id,
      selected_option: selectedOption,
      confidence: confidence,
      time_spent_seconds: timeSpent
    })
  });
  
  // 2. Keyingi savolni olish
  const nextQuestion = await fetch(
    `/testengine/sessions/${sessionId}/next-question/`,
    { headers: { 'Authorization': `Bearer ${access_token}` } }
  ).then(r => r.json());
  
  if (nextQuestion.question) {
    // Yangi savol ko'rsatish
    setCurrentQuestion(nextQuestion.question);
  } else {
    // Test tugash ekrani
    await finishTest();
  }
};
```

### Animation/States:
```
1. Question Loading: Spinner
2. Option Selected: Background color change + checkmark
3. Answer Submitted: Disable options, show "Keyingi >" button
4. Feedback (optional): 
   - Correct: ✅ Green background, animation
   - Wrong: ❌ Red background, show correct answer
```

---

## ✅ SCREEN 5: TEST RESULT / SUMMARY

### Layout:
```
┌──────────────────────────────────┐
│ ← TEST YAKUNLANDI                │ (Header)
├──────────────────────────────────┤
│                                  │
│          🎉 TABRIKLAYMIZ! 🎉     │ (Celebration - conditional)
│                                  │
│  ┌──────────────────────────────┐ │
│  │  📊 TEST NATIJALARI           │ │ (Summary card)
│  │  ════════════════════         │ │
│  │                              │ │
│  │  📈 Umumiy Ball: 95/100      │ │ (Large, 24px)
│  │  ✅ To'g'ri: 19/20           │ │ (Green)
│  │  ❌ Noto'g'ri: 1/20          │ │ (Red)
│  │  ⏱️ Vaqti: 30 minut 45 sec   │ │
│  │                              │ │
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │  💰 EARNED XP                 │ │ (XP card - Yellow)
│  │  ════════════════════         │ │
│  │                              │ │
│  │  + 10 XP (Test)              │ │
│  │  + 38 XP (Correct answers)   │ │ (5 XP x 19)
│  │  +  2 XP (Streak bonus)      │ │
│  │  ──────────────────          │ │
│  │  = 50 XP TOTAL 🚀            │ │
│  │                              │ │
│  │  New Total: 1,300 XP 📈      │ │
│  │                              │ │
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │  🎯 STREAKINGIZ               │ │
│  │  ════════════════════         │ │
│  │  ✅ 7 KUN KETMA-KETLIK!      │ │ (Green, large)
│  │  Eng uzun: 15 kun             │ │
│  │  [❄️ Freezni Ishlatish]        │ │ (Button if available)
│  │                              │ │
│  └──────────────────────────────┘ │
│                                  │
├──────────────────────────────────┤
│  QADIMGI SAVOLLARI TAKRORLASH     │
│  UCHUN REJA YARATILDI ✓           │
│                                  │
├──────────────────────────────────┤
│  ┌──────────────────────────────┐ │
│  │ HOME GA QAYTISH              │ │ (Primary button)
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │ DETALLNI KO'RISH             │ │ (Secondary button)
│  │ (Har bir savol-javob analyze)│ │
│  └──────────────────────────────┘ │
│                                  │
└──────────────────────────────────┘
```

### API Calls:
```javascript
// Test finish qilganda
const finishTest = async () => {
  const result = await fetch(
    `/testengine/sessions/${sessionId}/finish/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${access_token}`
      }
    }
  ).then(r => r.json());
  
  // Result ma'lumotlari:
  // - total_score, correct_count, incorrect_count, duration_seconds
  // - XP hisoblash va ko'rsatish
  // - Streak yangilash
};
```

---

## 📋 SCREEN 6: REVIEW / REPETITION (TAKRORLASH)

### Layout:
```
┌──────────────────────────────────┐
│ ← TAKRORLASH                      │ (Header)
├──────────────────────────────────┤
│                                  │
│  📅 BUGUN TAKRORLASH KERAK        │ (Title)
│  5 ta savol mavjud               │ (Subtitle)
│                                  │
├──────────────────────────────────┤
│                                  │
│  SAVOL 1/5                        │ (Progress)
│  ▓▓░░░░░░░░░░░░░░░░              │ (Progress bar)
│                                  │
│  📖 O'nchalik sanoq sistemasida   │ (Question)
│  10 nima degan ma'noga keladi?    │
│                                  │
│  ┌──────────────────────────────┐ │
│  │ ◯ A) O'n                     │ │ (Options)
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │ ◉ B) Bitta                   │ │
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │ ◯ C) Qo'shimcha              │ │
│  └──────────────────────────────┘ │
│                                  │
│  ISHONCH: [◉ Ishonch] [◯ Taxmin] │
│                                  │
├──────────────────────────────────┤
│  ┌──────────────────────────────┐ │
│  │ ✅ TO'G'RI JAVOB BERISH      │ │ (Green button)
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │ ❌ NOTO'G'RI JAVOB BERISH    │ │ (Red button)
│  └──────────────────────────────┘ │
│                                  │
│  📊 Stabilnost: 3.0 kun          │ (Info)
│  📅 Keyingi: 2026-08-13          │ (Info)
│                                  │
└──────────────────────────────────┘
```

### API Implementation:
```javascript
// Takrorlash javobini submit qilish
const submitReview = async (isCorrect) => {
  const response = await fetch(
    `/progress/reviews/${reviewCardId}/submit/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${access_token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        is_correct: isCorrect,
        confidence: selectedConfidence
      })
    }
  ).then(r => r.json());
  
  // Response:
  // {
  //   "id": 1,
  //   "stability_days": 6.0,  // FSRS yangilandi
  //   "next_review_date": "2026-08-16"  // Yangi sana
  // }
  
  // Keyingi reviewga o'tish yoki tamomlash
  if (reviewCount < totalReviews) {
    loadNextReview();
  } else {
    showCompletionScreen();
  }
};
```

---

## 🔥 SCREEN 7: STREAK

### Layout:
```
┌──────────────────────────────────┐
│ ← STATISTIKA                      │ (Header)
├──────────────────────────────────┤
│                                  │
│          🔥 STREAKINGIZ 🔥        │ (Title - 24px)
│                                  │
│  ┌──────────────────────────────┐ │
│  │                              │ │ (Big stat card)
│  │        📊 7 KUN               │ │ (Large number - 48px)
│  │                              │ │
│  │  Ketma-ketlik o'spirladi      │ │ (Description)
│  │                              │ │
│  │  Og'zingizni qasda ushlamang! │ │ (Motivational)
│  │                              │ │
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │  📈 Eng uzun: 15 kun          │ │ (Record)
│  │  📅 Oxirgi faollik: 2026-08-10│ │ (Last activity)
│  │  ❄️ Freeze: 1 qoldi            │ │ (Freezes left)
│  └──────────────────────────────┘ │
│                                  │
│  🎯 SHUNGA ERISHISH:              │ (Achievements)
│  ☐ 10 kun streak                 │ (Milestone)
│  ☐ 30 kun streak                 │ (Grayed out)
│  ☐ 100 kun streak                │ (Grayed out)
│                                  │
├──────────────────────────────────┤
│  ┌──────────────────────────────┐ │
│  │ ❄️ FREEZNI ISHLATISH          │ │ (Freeze button)
│  │ (Streak uzilishini prevent)  │ │
│  │ Qolgan: 1 marta               │ │
│  └──────────────────────────────┘ │
│                                  │
│  [Freeze uchun premium sotib ol]  │ (Premium upsell - if none)
│                                  │
└──────────────────────────────────┘
```

### Button Actions:
```javascript
const handleFreeze = async () => {
  if (streak.freezes_available <= 0) {
    showAlert("Freeze yo'q! Premium olish kerak");
    return;
  }
  
  const response = await fetch('/progress/streak/freeze/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`
    }
  }).then(r => r.json());
  
  // Response: 
  // {
  //   "current_streak": 7,  // O'zgarmadi
  //   "freezes_available": 0  // Kamaydi
  // }
  
  showSuccess("Streak saqlandi! ❄️");
};
```

---

## 💰 SCREEN 8: PREMIUM / BILLING

### Layout:
```
┌──────────────────────────────────┐
│ ← PREMIUM GA YO'NALTIRING         │ (Header)
├──────────────────────────────────┤
│                                  │
│  ✨ PREMIUM O'ZINGIZNI KO'P        │ (Title)
│  QOBILASHTIRADI ✨                │
│                                  │
│  BEPUL → PREMIUM UCHUN:           │ (Benefits)
│  ✓ Cheksiz freeze (bugun 3 ta)   │
│  ✓ Exam mode (vaqt bilan test)   │ (Green checkmarks)
│  ✓ Savollar analitikasi          │
│  ✓ Mentor yordam                 │
│                                  │
├──────────────────────────────────┤
│  REJALARNI TANLANG:               │ (Plans section)
│                                  │
│  ┌──────────────────────────────┐ │
│  │  FREE                        │ │ (Free plan)
│  │  ════════════════════        │ │ BG: #F5F5F5
│  │  $0 / ∞                      │ │
│  │  ✓ Cheksiz test yechish      │ │
│  │  ✓ Asosiy statistika         │ │
│  │  ✗ Freeze                    │ │
│  │  ✗ Exam mode                 │ │
│  │  [SIZDA BU REJA]             │ │
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │  MONTHLY                     │ │ (Recommended - highlighted)
│  │  ════════════════════        │ │ BG: #E3F2FD
│  │  $2.99 / OY                  │ │ Border: 2px #007AFF
│  │  ✓ Barchasi (Free-ga)        │ │
│  │  ✓ Cheksiz freeze            │ │ Gold badge: "ASOSIY"
│  │  ✓ Exam mode                 │ │
│  │  ✓ Analitika                 │ │
│  │  [SOTIB OLISH] (Blue button) │ │
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │  YEARLY                      │ │ (Best value)
│  │  ════════════════════        │ │ BG: #F5F5F5
│  │  $29.99 / YIL                │ │
│  │  (Oy bo'yicha: $2.50) 📉    │ │
│  │  ✓ Barchasi MONTHLY-ga       │ │
│  │  ✓ + 3 ay BEPUL!             │ │ (Bonus badge)
│  │  [SOTIB OLISH]               │ │
│  └──────────────────────────────┘ │
│                                  │
├──────────────────────────────────┤
│  ❓ Savollar? Yoki muammo?        │ (Support)
│  📧 Support: admin@...            │
│                                  │
└──────────────────────────────────┘
```

### Purchase Flow:
```javascript
// 1. Plan tanlash
const handleBuyPlan = async (planId) => {
  // First: Subscription yaratish
  const subResponse = await fetch('/billing/subscriptions/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ plan_id: planId })
  }).then(r => r.json());
  
  // 2. Payment flow boshlash
  navigateTo('/payment', {
    subscriptionId: subResponse.id,
    amount: planPrice,
    provider: 'payme'  // yoki 'click'
  });
};

// 2. Payment qilish
const handlePayment = async () => {
  const paymentResponse = await fetch('/billing/payments/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      subscription_id: subscriptionId,
      provider: 'payme',
      amount: amount
    })
  }).then(r => r.json());
  
  // Payment provider-ga yo'naltirish
  redirectToPaymentProvider(paymentResponse.provider_transaction_id);
};

// 3. Admin tasdiq (backend to'liq qiladi yoki webhook)
// POST /billing/payments/{id}/approve/
```

---

## 🏆 SCREEN 9: LEADERBOARD

### Layout:
```
┌──────────────────────────────────┐
│ ← REYTING                         │ (Header)
├──────────────────────────────────┤
│                                  │
│  🏆 HAFTALIK TOP 100              │ (Title)
│  Bu hafta eng faol talabalar      │
│                                  │
│  📊 FILTRLASH:                    │
│  [Bu hafta] [Oylik] [Umumiy]     │ (Time filter)
│                                  │
├──────────────────────────────────┤
│                                  │
│  ┌──────────────────────────────┐ │
│  │ 🥇 1. ALI ABDURAHMON          │ │ (Gold medal)
│  │    ⭐⭐⭐⭐⭐ 500 XP             │ │ Stars + XP
│  │    🔥 7 kun streak           │ │ Streak
│  │    Avatar: [👨]               │ │ Small avatar
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │ 🥈 2. VALI VALIYEV            │ │ (Silver)
│  │    ⭐⭐⭐⭐ 450 XP              │ │
│  │    🔥 5 kun streak           │ │
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │ 🥉 3. SOHIB SOHANOV           │ │ (Bronze)
│  │    ⭐⭐⭐ 400 XP               │ │
│  │    🔥 3 kun streak           │ │
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │ 4. ZARRINA Z.                 │ │ (Regular)
│  │    350 XP                      │ │ (No medal)
│  │    🔥 1 kun streak           │ │
│  └──────────────────────────────┘ │
│  ...                              │ (Scrollable list)
│                                  │
│  ┌──────────────────────────────┐ │
│  │ 47. SANA QODIROV (SIZ)        │ │ (Highlighted - current user)
│  │     ✓ 120 XP                  │ │ Green bg
│  │     🔥 2 kun streak           │ │
│  └──────────────────────────────┘ │
│                                  │
└──────────────────────────────────┘
```

### Data Loading:
```javascript
useEffect(() => {
  const fetchLeaderboard = async () => {
    const response = await fetch(
      '/progress/leaderboard/weekly/',
      {
        headers: { 'Authorization': `Bearer ${access_token}` }
      }
    ).then(r => r.json());
    
    setLeaderboard(response.results);
  };
  
  fetchLeaderboard();
  // Auto-refresh har 5 minutda
  const interval = setInterval(fetchLeaderboard, 5 * 60 * 1000);
  return () => clearInterval(interval);
}, []);
```

---

## 👤 SCREEN 10: PROFILE

### Layout:
```
┌──────────────────────────────────┐
│ ← PROFIL                          │ (Header)
├──────────────────────────────────┤
│          [AVATAR]                 │ (Large avatar - 100px)
│       ALI ABDURAHMON              │ (Name - 20px)
│       ali@example.com             │ (Email - 14px)
│                                  │
│  STATISTIKA:                      │
│  ┌──────────┐ ┌──────────┐       │
│  │ 💎 1250  │ │ 🔥 7     │ (2 cards)
│  │ XP TOTAL │ │ STREAK   │
│  └──────────┘ └──────────┘       │
│                                  │
│  ┌──────────┐ ┌──────────┐       │
│  │ 📊 42    │ │ 🏆 47    │
│  │ TEST     │ │ RANK     │
│  │ YAKUNLADI│ │ (WEEKLY) │
│  └──────────┘ └──────────┘       │
│                                  │
├──────────────────────────────────┤
│  MA'LUMOTLAR:                     │
│                                  │
│  Region: Tashkent                │ (Info rows)
│  Maqsadi: Computer Science        │
│  Premium: Faol (20 kun qolgan)    │
│                                  │
├──────────────────────────────────┤
│  ┌──────────────────────────────┐ │
│  │ ⚙️ SOZLAMALAR                 │ │ (Settings button)
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │ 📞 YARDAMGA MUROJAAT          │ │
│  └──────────────────────────────┘ │
│                                  │
│  ┌──────────────────────────────┐ │
│  │ 🚪 CHIQISH                    │ │ (Logout button - Red)
│  └──────────────────────────────┘ │
│                                  │
└──────────────────────────────────┘
```

### API Calls:
```javascript
// Profile data loading
useEffect(() => {
  const fetchProfile = async () => {
    const [user, stats] = await Promise.all([
      fetch('/api/auth/me/', {...}).then(r => r.json()),
      fetch('/progress/xp/summary/', {...}).then(r => r.json())
    ]);
    
    setUser(user);
    setStats(stats);
  };
  
  fetchProfile();
}, []);

// Logout
const handleLogout = async () => {
  await fetch('/api/auth/logout/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ refresh: refresh_token })
  });
  
  localStorage.clear();
  navigate('/login');
};
```

---

## 📱 RESPONSIVE DESIGN CONSIDERATIONS

### Mobile (375px - 480px):
- Single column layout
- Large touch targets (min 44x44px)
- Simplified navigation (hamburger menu)
- Stack cards vertically

### Tablet (768px - 1024px):
- 2-column grid for cards
- Side-by-side layouts
- Larger text sizes

### Desktop (1024px+):
- 3-4 column layouts
- Sidebar navigation
- Advanced filters

---

## 🎨 COMPONENT LIBRARY

### BUTTONS:
```
Primary Button:
  BG: #007AFF
  Text: White
  Padding: 12px 24px
  Border-radius: 8px
  Height: 44px
  Font: 16px Semibold
  
Secondary Button:
  BG: #F5F5F5
  Text: #007AFF
  Border: 1px #007AFF
  
Danger Button:
  BG: #FF3B30
  Text: White
  
Loading State:
  Opacity: 0.5
  Cursor: not-allowed
```

### CARDS:
```
Shadow: 0 2px 8px rgba(0,0,0,0.1)
Border-radius: 12px
Padding: 16px
Margin-bottom: 12px
Background: White
```

### INPUTS:
```
Height: 44px
Border: 1px #CCCCCC
Border-radius: 8px
Padding: 12px
Font: 16px
Focus: Border-color #007AFF, Shadow
```

### BADGES:
```
Background: #E3F2FD
Color: #007AFF
Padding: 4px 8px
Border-radius: 4px
Font: 12px Semibold
```

---

## ✨ ANIMATIONS & INTERACTIONS

### Loading States:
```
Skeleton loading (gray placeholder)
Spinner (rotating icon - 20px)
Progress bars (smooth animation)
```

### Transitions:
```
Page transitions: 300ms fade
Button hover: 200ms color change
List scroll: Smooth scroll behavior
```

### Haptic Feedback (Mobile):
```
Button press: Light haptic
Answer selection: Medium haptic
Success: Heavy haptic
Error: Double light haptic
```

---

**Tayyor! 🎉 Bu guide-ni Figma-da component-lar sifatida yaratib, prototype qiling!**
