# 🏗️ RATING VA DASHBOARD SISTEMI - ARXITEKTURA

---

## 📐 DATABASE SXEMASI

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ACCOUNT (Foydalanuvchi)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  User (email, google_id, full_name, xp_total, role, ...)                   │
│  Rollari: STUDENT, MENTOR, ADMIN, SUPPORT                                   │
└─────────────────────────────────────────────────────────────────────────────┘
  │
  ├──────────────────────────┬──────────────────────────┬──────────────────────┐
  │                          │                          │                      │
  ▼                          ▼                          ▼                      ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│    PROGRESS      │  │    TESTENGINE    │  │    RATING        │  │   DASHBOARD      │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│ • Streak         │  │ • TestSession    │  │ • Rating         │  │ • MentorStudent  │
│ • ReviewCard     │  │ • Answer         │  │ • RatingHistory  │  │ • MentorAlert    │
│ • XPTransaction  │  │ • TestResult     │  │ • TopicRating    │  │ • Analytics      │
│                  │  │                  │  │ • SubjectRating  │  │ • DashboardAccess│
│                  │  │                  │  │ • Leaderboard    │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## 📊 RATING MODELS TUZILISHI

```
┌─────────────────────────────────────────────────────────────────┐
│                      RATING MODEL                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  user: ForeignKey(User)                                         │
│  period: 'daily' | 'weekly' | 'all_time'                       │
│  stars: 0.0-5.0 (⭐ XP'dan hisoblangan)                        │
│  tests_completed: PositiveIntegerField                          │
│  correct_answers: PositiveIntegerField                          │
│  incorrect_answers: PositiveIntegerField                        │
│  rank: PositiveIntegerField (1-N leaderboard'da)               │
│  period_start_date: DateField                                   │
│  period_end_date: DateField                                     │
│                                                                 │
│  Unique Together: (user, period, period_start_date, end_date)  │
│  Ordering: -stars, -tests_completed                             │
│  Indexes: (period, -stars), (period, period_start_date)        │
└─────────────────────────────────────────────────────────────────┘
         │
         │ has many
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   RATING HISTORY MODEL                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  user: ForeignKey(User)                                         │
│  rating: ForeignKey(Rating)                                     │
│  previous_stars: FloatField                                     │
│  new_stars: FloatField                                          │
│  stars_change: FloatField (+0.5, -0.2, etc.)                   │
│  previous_rank: PositiveIntegerField                            │
│  new_rank: PositiveIntegerField                                 │
│  reason: CharField (O'zgarish sababi)                           │
│  test_session: ForeignKey(TestSession, nullable)               │
│  period: CharField (qaysi davr yangilandi)                      │
│                                                                 │
│  Ordering: -created_at                                          │
│  Indexes: (user, -created_at), (period, -created_at)           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 REYTING HISOB-KITOB JARAYONI

```
┌──────────────────┐
│  Test Yakunlandi │
│   (TestResult)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  Answers'ni olish va stars hisoblash      │
│  Formula: (To'g'ri - Noto'g'ri * 0.5)   │
│           ────────────────────────────    │
│               Jami Savol          × 5    │
└────────┬─────────────────────────────────┘
         │
         ├─────────────────┬────────────────┬─────────────────┐
         │                 │                │                 │
         ▼                 ▼                ▼                 ▼
    ┌─────────┐   ┌──────────────┐  ┌─────────────┐  ┌──────────────┐
    │ Daily   │   │   Weekly     │  │  All-Time   │  │ TopicRating  │
    │ Rating  │   │   Rating     │  │   Rating    │  │ SubjectRating│
    └────┬────┘   └──────┬───────┘  └──────┬──────┘  └──────┬───────┘
         │                │                 │                │
         │ (stars changed)│(stars changed)  │(stars changed) │
         ▼                ▼                 ▼                ▼
    ┌──────────────────────────────────────────────────────────┐
    │           Create RatingHistory Entry                     │
    │  - previous_stars, new_stars, stars_change               │
    │  - reason: "Kunlik test yakunlandi", etc.               │
    │  - test_session reference                                │
    └────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
    ┌──────────────────────────────────────────────────────────┐
    │         Recalculate Leaderboard                          │
    │  - Barcha users'ni -stars bo'yicha sort qilish          │
    │  - Rank qanday o'zgarganini saqlash                     │
    │  - Period bo'yicha (daily, weekly, all_time)            │
    └──────────────────────────────────────────────────────────┘
```

---

## 👥 DASHBOARD MODELS TUZILISHI

```
┌─────────────────────────────────────────┐
│       MENTOR STUDENT MODEL              │
├─────────────────────────────────────────┤
│                                         │
│  mentor: ForeignKey(User, role=MENTOR) │
│  student: ForeignKey(User, role=STU)   │
│  assigned_at: DateTimeField             │
│  is_active: BooleanField                │
│  notes: TextField                       │
│                                         │
│  Unique: (mentor, student)              │
│  Ordering: -assigned_at                 │
└────────┬────────────────────────────────┘
         │
         │ has many
         ▼
┌─────────────────────────────────────────┐
│       MENTOR ALERT MODEL                │
├─────────────────────────────────────────┤
│                                         │
│  mentor: ForeignKey(User)               │
│  student: ForeignKey(User)              │
│  alert_type:                            │
│    • LOW_PERFORMANCE                    │
│    • NO_ACTIVITY (3 kun test yo'q)     │
│    • LOW_RATING (reyting past)          │
│    • STREAK_BROKEN                      │
│    • NEEDS_REVIEW                       │
│                                         │
│  status: OPEN | RESOLVED | IGNORED      │
│  message: TextField                     │
│  action_taken: TextField                │
│  test_session: ForeignKey (nullable)   │
│                                         │
│  Ordering: -created_at                  │
│  Indexes: (mentor, status), (student)  │
└─────────────────────────────────────────┘
```

---

## 📈 ANALYTICS MODELS

```
┌────────────────────────────────────────────────┐
│      ANALYTICS SUMMARY MODEL                   │
├────────────────────────────────────────────────┤
│                                                │
│  date: DateField                               │
│  timeframe: DAILY | WEEKLY | MONTHLY | YEARLY │
│                                                │
│  FOYDALANUVCHILAR:                            │
│  • total_users                                 │
│  • active_users                                │
│  • new_users                                   │
│                                                │
│  TESTLAR:                                      │
│  • total_tests_completed                       │
│  • average_accuracy                            │
│  • average_rating                              │
│                                                │
│  OBUNALAR:                                     │
│  • active_subscriptions                        │
│  • expired_subscriptions                       │
│  • total_revenue                               │
│                                                │
│  ENGAGEMENT:                                   │
│  • engagement_rate (%)                         │
│  • retention_rate (%)                          │
│  • top_subject_id                              │
│                                                │
│  Unique: (date, timeframe)                     │
│  Ordering: -date                               │
└────────────────────────────────────────────────┘
```

---

## 🔐 DASHBOARD ACCESS MODEL

```
┌────────────────────────────────────────────┐
│    DASHBOARD ACCESS LOG MODEL              │
├────────────────────────────────────────────┤
│                                            │
│  user: ForeignKey(User)                    │
│  dashboard_type:                           │
│    • MENTOR      (mentor dashboard)        │
│    • ADMIN       (admin dashboard)         │
│    • ANALYTICS   (analytics dashboard)     │
│                                            │
│  accessed_at: DateTimeField (auto)         │
│  ip_address: GenericIPAddressField         │
│  duration_minutes: PositiveIntegerField    │
│                                            │
│  Ordering: -accessed_at                    │
│  Indexes: (user, dashboard_type), (date)  │
└────────────────────────────────────────────┘
```

---

## 🔄 DATA FLOW: TEST COMPLETION → RATING UPDATE

```
┌───────────────────┐
│ Student Test Ends │
└────────┬──────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ TestResult Model Created (Signal Event) │
│ • correct_count: 12                     │
│ • incorrect_count: 3                    │
│ • total_score: 80                       │
└────────┬────────────────────────────────┘
         │
         ▼
    Signal Handler Triggered
    (progress/signals.py → @receiver(post_save, TestResult))
         │
         ├─ Calculate stars from test result
         │  Formula: (12 - 3*0.5) / 15 * 5 = 3.6 ⭐
         │
         ├─ Update TopicRating (if exists)
         │  • Recalculate average stars for topic
         │  • Update accuracy percentage
         │
         ├─ Update SubjectRating
         │  • Recalculate average stars for subject
         │  • Update topics_completed
         │
         ├─ Update Daily Rating
         │  • Create if not exists
         │  • Recalculate today's average stars
         │  • If changed: Create RatingHistory entry
         │
         ├─ Update Weekly Rating
         │  • Calculate week boundaries
         │  • Recalculate week average stars
         │  • If changed: Create RatingHistory entry
         │
         ├─ Update All-Time Rating
         │  • Recalculate all user's average stars
         │  • If changed: Create RatingHistory entry
         │
         └─ Recalculate Leaderboard
            • Sort users by -stars, -tests_completed
            • Update rank for each user
            • Update Leaderboard entries
         │
         ▼
    All Changes Saved to Database ✅
         │
         ├─ Rating records updated
         ├─ RatingHistory records created
         ├─ Leaderboard records updated
         └─ User's ranking may have changed
```

---

## 🎨 ADMIN PANEL LAYOUT

```
Django Admin Dashboard
├── RATING
│   ├── Ratings (list view)
│   │   ├── Filter by: period, date
│   │   ├── Search by: user email, name
│   │   └── Display: stars (⭐), tests, accuracy, rank
│   │
│   ├── Rating Histories
│   │   ├── Filter by: period, date
│   │   ├── Display: ⬆️⬇️ changes, reason
│   │   └── Link to: test_session
│   │
│   ├── Topic Ratings
│   │   ├── Display: Fan → Mavzu
│   │   └── Show: stars, accuracy%
│   │
│   ├── Subject Ratings
│   │   ├── Display: Fan name
│   │   └── Show: stars, topics_completed
│   │
│   └── Leaderboards
│       ├── Display: 🥇🥈🥉 medallary
│       ├── Filter: period, date
│       └── Rank: 1-100
│
└── DASHBOARD
    ├── Mentor Students
    │   ├── Display: mentor ↔ student
    │   └── Show: status (✓/✗), assigned_at
    │
    ├── Mentor Alerts
    │   ├── Alert Types (color-coded):
    │   │   🔴 Low Performance
    │   │   🔴 No Activity
    │   │   🔴 Low Rating
    │   │   🟣 Streak Broken
    │   │   🔵 Needs Review
    │   │
    │   └── Status: ⚪ Open / ✅ Resolved / ⭕ Ignored
    │
    ├── Analytics Summaries
    │   ├── Timeframe: Daily, Weekly, Monthly, Yearly
    │   ├── Display: users, tests, revenue, rating
    │   └── Engagement & retention rates
    │
    └── Dashboard Access
        ├── Display: user, dashboard_type
        ├── Time: accessed_at, duration
        └── IP: ip_address
```

---

## 🔗 RELATIONSHIP DIAGRAM

```
                    User (account.User)
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
    ┌────────┐        ┌──────────┐      ┌─────────────┐
    │ Rating │        │TopicRating   │SubjectRating│
    └────┬───┘        └──────────┘   └─────────────┘
         │                │                  │
    ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
    │ Lease    │       │ Topic   │      │ Subject │
    │ board    │       └─────────┘      └─────────┘
    └─────────┘

    User
     │
     ├─ mentored_students (as Mentor)
     │   └─ MentorStudent ──┬─ student
     │                      └─ MentorAlert
     │
     └─ alerts (as Mentor)
        └─ MentorAlert ──┬─ student
                         └─ test_session

    Rating ──┬─ RatingHistory
             └─ (Daily, Weekly, All-time per user)

    Leaderboard ──┬─ user
                  └─ (Ranked by period and date)
```

---

## 📊 EXAMPLE DATA

### Rating Table:
```
user_id | period  | period_start | period_end | stars | tests | correct | rank
--------|---------|--------------|-----------|-------|-------|---------|-----
   1    | daily   | 2026-08-11   | 2026-08-11 | 4.2   |  10   |   8    |  3
   1    | weekly  | 2026-08-11   | 2026-08-17 | 3.8   |  47   |  36    |  7
   1    | all_time|              |           | 3.5   |  450  | 315    | 25
   2    | daily   | 2026-08-11   | 2026-08-11 | 4.8   |  8    |   7    |  1
```

### Leaderboard Table:
```
period   | rank | user_id | stars | tests | date
---------|------|---------|-------|-------|----------
daily    |  1   |   2     | 4.8   |  8    | 2026-08-11
daily    |  2   |   5     | 4.5   |  12   | 2026-08-11
daily    |  3   |   1     | 4.2   |  10   | 2026-08-11
weekly   |  1   |   3     | 4.1   |  67   | 2026-08-11
weekly   |  2   |   1     | 3.8   |  47   | 2026-08-11
```

---

**✅ FULL ARCHITECTURE READY!**

