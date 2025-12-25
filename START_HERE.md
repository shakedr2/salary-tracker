# 🚀 הוראות הפעלה - YLM Salary Tracker

## ⚠️ בעיה ידועה
אם אתה משתמש ב-Windows עם PowerShell, יש בעיה עם נתיבים בעברית.

## ✅ פתרון מהיר

### אפשרות 1: הפעלה דרך CMD (מומלץ)
1. פתח **Command Prompt** (CMD) - לא PowerShell
2. נווט לתיקייה:
   ```
   cd "C:\Users\shake\OneDrive\Desktop\קורס דבופס\salary_tracker"
   ```
3. הפעל:
   ```
   python run_app.py
   ```
   או:
   ```
   python backend\run.py
   ```

### אפשרות 2: הפעלה דרך קובץ Batch
1. לחץ כפול על `start_app.bat`
2. האפליקציה תרוץ אוטומטית

### אפשרות 3: הפעלה ישירה
1. פתח **Command Prompt**
2. הפעל:
   ```
   cd /d "C:\Users\shake\OneDrive\Desktop\קורס דבופס\salary_tracker"
   python -m backend.app
   ```

## 📝 לפני ההפעלה - בדוק!

### 1. ודא שקובץ `.env` קיים ומכיל:
```env
YLM_USERNAME=השם_שלך_כאן
YLM_PASSWORD=הסיסמה_שלך_כאן
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false
```

### 2. ודא שהתלויות מותקנות:
```bash
pip install -r requirements.txt
```

## 🌐 לאחר ההפעלה

פתח בדפדפן:
```
http://localhost:5000
```

או בדוק את ה-health endpoint:
```
http://localhost:5000/api/health
```

## ❌ פתרון בעיות

### שגיאה: "ModuleNotFoundError: No module named 'backend'"
**פתרון:** ודא שאתה בתיקייה הנכונה (`salary_tracker`)

### שגיאה: "Missing YLM credentials"
**פתרון:** מלא את `YLM_USERNAME` ו-`YLM_PASSWORD` בקובץ `.env`

### שגיאה: "Address already in use"
**פתרון:** שנה את הפורט ב-`.env`:
```env
FLASK_PORT=5001
```

### האפליקציה לא נפתחת בדפדפן
**פתרון:** 
1. ודא שהאפליקציה רצה (תראה הודעות בקונסול)
2. נסה `http://127.0.0.1:5000` במקום `localhost`
3. בדוק את חומת האש

## 📞 עזרה נוספת

אם עדיין יש בעיות, הרץ:
```bash
python test_app.py
```

זה יראה לך בדיוק מה הבעיה.

