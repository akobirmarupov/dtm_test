## TESTENGINE API - POSTMAN SHABLONLARI

### 1. Yangi Test Sessiyasi Yaratish
**POST** `/testengine/sessions/`

**Body (raw JSON):**
```json
{
    "subject": 1,
    "mode": "practice"
}
```

**mode qiymatlari:**
- `"practice"` - O'rganish rejimi
- `"exam"` - Imtihon rejimi

---

### 2. Bitta Javob Yuborish
**POST** `/testengine/sessions/{session_id}/answers/`

**Body (raw JSON):**
```json
{
    "question": 5,
    "selected_option": "B",
    "is_correct": true,
    "confidence": "sure",
    "time_spent_seconds": 45
}
```

**Tushuntirish:**
- `question` - Savol ID
- `selected_option` - Javob varianti (A, B, C, D, E, F)
- `is_correct` - To'g'ri/noto'g'ri (true/false)
- `confidence` - Ishonch darajasi:
  - `"sure"` - Ishonchli
  - `"guess"` - Taxmin
  - `""` - Bo'sh (optional)
- `time_spent_seconds` - Sarflangan vaqt (sekund)

---

### 3. Ko'p Javobni Birdan Yuborish (Offline-Sync)
**POST** `/testengine/sessions/{session_id}/answers/bulk/`

**Body (raw JSON):**
```json
{
    "answers": [
        {
            "question": 1,
            "selected_option": "A",
            "is_correct": true,
            "confidence": "sure",
            "time_spent_seconds": 30
        },
        {
            "question": 2,
            "selected_option": "C",
            "is_correct": false,
            "confidence": "guess",
            "time_spent_seconds": 45
        },
        {
            "question": 3,
            "selected_option": "B",
            "is_correct": true,
            "confidence": "",
            "time_spent_seconds": 25
        }
    ]
}
```

---

### 4. Sessiya Holatini Yangilash
**PATCH** `/testengine/sessions/{session_id}/`

**Body (raw JSON):**
```json
{
    "mode": "exam"
}
```

---

### 5. Sessiyani Yakunlash (Finish)
**POST** `/testengine/sessions/{session_id}/finish/`

**Body (raw JSON):**
```json
{}
```

*Yoki bo'sh body qoldirish mumkin*

---

### 6. Offline Javoblarni Sinxronlash
**POST** `/testengine/sessions/{session_id}/sync/`

**Body (raw JSON):**
```json
{
    "answers": [
        {
            "question": 10,
            "selected_option": "D",
            "is_correct": true,
            "confidence": "sure",
            "time_spent_seconds": 50
        },
        {
            "question": 11,
            "selected_option": "A",
            "is_correct": false,
            "confidence": "guess",
            "time_spent_seconds": 60
        }
    ]
}
```

---

## GET ENDPOINTS (Faqat batafsil uchun)

### Sessiyalar Ro'yxati
**GET** `/testengine/sessions/`

**Query Parameters (optional):**
```
?user=1
?mode=practice
?subject=1
?is_finished=true
?page=1
?page_size=20
```

---

### Sessiya Tafsiloti
**GET** `/testengine/sessions/{session_id}/`

---

### Keyingi Savol (Adaptiv)
**GET** `/testengine/sessions/{session_id}/next-question/`

---

### Sessiyaning Javoblari
**GET** `/testengine/sessions/{session_id}/answers/`

**Query Parameters (optional):**
```
?is_correct=true
?confidence=sure
?time_spent_min=30
?time_spent_max=100
?page=1
```

---

### Test Natijalari
**GET** `/testengine/results/`

**Query Parameters (optional):**
```
?total_score_min=50
?total_score_max=100
?correct_count_min=5
?page=1
```

---

### Mening Natijalari (Progress)
**GET** `/testengine/results/my-results/`

---

## HEADERS (Barcha Requestlar)

```json
{
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    "Content-Type": "application/json"
}
```

---

## BILLING API - POSTMAN SHABLONLARI

### 1. Yangi Rejani Yaratish
**POST** `/billing/plan/`

**Body (raw JSON):**
```json
{
    "name": "Premium Plan",
    "price": "9.99",
    "duration_days": 30
}
```

---

### 2. Rejani Yangilash (PUT)
**PUT** `/billing/plan/{id}/`

**Body (raw JSON):**
```json
{
    "name": "Premium Plan Updated",
    "price": "12.99",
    "duration_days": 30
}
```

---

### 3. Rejani Qismi Yangilash (PATCH)
**PATCH** `/billing/plan/{id}/`

**Body (raw JSON):**
```json
{
    "price": "14.99"
}
```

---

### 4. Yangi Obuna (Subscription) Yaratish
**POST** `/billing/subscriptions/`

**Body (raw JSON):**
```json
{
    "plan_id": 1
}
```

---

### 5. Obunani Yangilash (PATCH)
**PATCH** `/billing/subscriptions/{id}/`

**Body (raw JSON):**
```json
{
    "status": "active",
    "starts_at": "2026-08-10T10:00:00Z",
    "expires_at": "2026-09-10T10:00:00Z"
}
```

---

### 6. Obunani Bekor Qilish
**POST** `/billing/subscriptions/{id}/cancel/`

**Body (raw JSON):**
```json
{}
```

---

### 7. Yangi To'lov (Payment) Yaratish
**POST** `/billing/payments/`

**Body (raw JSON):**
```json
{
    "subscription": 1,
    "provider": "payme",
    "provider_transaction_id": "TXN123456789",
    "amount": "9.99"
}
```

---

### 8. To'lovni Yangilash (PATCH)
**PATCH** `/billing/payments/{id}/`

**Body (raw JSON):**
```json
{
    "status": "success"
}
```

---

### 9. To'lovni Tasdiqlash (Approve)
**POST** `/billing/payments/{id}/approve/`

**Body (raw JSON):**
```json
{}
```

---

### 10. To'lovni Rad Etish (Reject)
**POST** `/billing/payments/{id}/reject/`

**Body (raw JSON):**
```json
{}
```

---

## BILLING - STATUS QIYMATLARI

**Subscription Status:**
- `"active"` - Faol
- `"expired"` - Muddati o'tgan
- `"cancelled"` - Bekor qilingan

**Payment Status:**
- `"pending"` - Kutilmoqda
- `"success"` - Muvaffaqiyatli
- `"failed"` - Muvaffaqiyatsiz

**Payment Provider:**
- `"payme"` - Payme
- `"click"` - Click

---

## ERROR RESPONSES

### 400 Bad Request
```json
{
    "detail": "Tugagan sessiyaga javob qo'shish mumkin emas."
}
```

### 404 Not Found
```json
{
    "detail": "Bunday sessiya mavjud emas."
}
```

### 500 Internal Server Error
```json
{
    "detail": "Javob saqlashda xatolik yuz berdi."
}
```

---

## EXAMPLES

### Sessiyadagi Har Bir Javobga Bulk Yuborish Misoli

**1-qadam:** Sessiya yaratish
```bash
POST /testengine/sessions/
{
    "subject": 1,
    "mode": "practice"
}
```

**Response:** `session_id = 15`

---

**2-qadam:** Javoblarni offline topish (mobil app'da)
- Savollar: 1, 2, 3, 4, 5
- Javoblar: A, B, A, C, B

---

**3-qadam:** Bulk yuborish
```bash
POST /testengine/sessions/15/answers/bulk/
{
    "answers": [
        {"question": 1, "selected_option": "A", "is_correct": true, "confidence": "sure", "time_spent_seconds": 25},
        {"question": 2, "selected_option": "B", "is_correct": true, "confidence": "sure", "time_spent_seconds": 30},
        {"question": 3, "selected_option": "A", "is_correct": false, "confidence": "guess", "time_spent_seconds": 40},
        {"question": 4, "selected_option": "C", "is_correct": true, "confidence": "sure", "time_spent_seconds": 35},
        {"question": 5, "selected_option": "B", "is_correct": true, "confidence": "sure", "time_spent_seconds": 28}
    ]
}
```

---

**4-qadam:** Sessiyani yakunlash
```bash
POST /testengine/sessions/15/finish/
{}
```

---

**5-qadam:** Natijalari ko'rish
```bash
GET /testengine/results/
```

Bu misolda:
- Umumiy savol: 5
- To'g'ri javob: 4
- Noto'g'ri javob: 1
- Ball: 4/5 = 80%
