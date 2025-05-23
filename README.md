# מערכת קיבוע זכויות

מערכת לניהול וחישוב זכויות פנסיוניות, מענקים, והיוונים.

## התקנה

1. התקנת תלויות:

```bash
pip install -r requirements.txt
```

2. הפעלת המערכת:

```bash
python run.py
```

המערכת תפעל על פורט 5001: http://localhost:5001

## מבנה המערכת

### מודל נתונים

- **Client** - נתוני לקוח
- **Grant** - מענקים פטורים
- **Pension** - קצבאות
- **Commutation** - היוונים פטורים

### פונקציונליות עיקרית

1. **חישוב גיל זכאות** - חישוב גיל זכאות לפי מין ותחילת קצבה
2. **הצמדת מענקים** - הצמדת מענקים למדד הלמ"ס מתאריך המענק לתאריך הזכאות
3. **חישוב חלק יחסי** - חישוב החלק היחסי של תקופת העבודה מתוך 32 השנים האחרונות שקדמו לגיל הזכאות
4. **חישוב פגיעה בתקרה** - חישוב הפגיעה בתקרת ההון הפטורה בהתאם למענק המוצמד והחלק היחסי

## ממשק API

### לקוחות

- `GET /api/clients` - שליפת כל הלקוחות
- `GET /api/clients/{id}` - שליפת לקוח לפי מזהה
- `POST /api/clients` - יצירת לקוח חדש

### חישובים

- `POST /api/calculate-eligibility-age` - חישוב גיל זכאות
- `POST /api/calculate-indexed-grant` - חישוב מענק מוצמד
- `POST /api/calculate-grant-impact` - חישוב פגיעת מענק בתקרת ההון הפטורה

## דוגמאות שימוש

### חישוב גיל זכאות

```
POST /api/calculate-eligibility-age
Content-Type: application/json

{
  "birth_date": "1960-01-01",
  "gender": "male",
  "pension_start": "2020-01-01"
}
```

### חישוב מענק מוצמד

```
POST /api/calculate-indexed-grant
Content-Type: application/json

{
  "amount": 100000,
  "grant_date": "2010-01-01",
  "eligibility_date": "2022-01-01"
}
```
