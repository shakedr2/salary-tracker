# 📤 הוראות העלאה ל-GitHub

## ⚠️ בעיה ידועה
PowerShell מתקשה עם נתיבים בעברית. השתמש באחת מהאפשרויות הבאות:

## ✅ פתרון 1: סקריפט Batch (הכי קל)

לחץ כפול על `push_to_github.bat` - זה יעשה הכל אוטומטית!

## ✅ פתרון 2: Command Prompt (CMD)

פתח **Command Prompt** (לא PowerShell) והרץ:

```cmd
cd "C:\Users\shake\OneDrive\Desktop\קורס דבופס\salary_tracker"

git init
git add backend/ frontend/ tests/ infra/ agent/ docs/ .github/ *.py *.md *.txt *.bat *.yml Dockerfile docker-compose.yml .gitignore
git commit -m "Major improvements: Add automated agent, observability, tests, CI/CD, and authentication"
git branch -M main
git remote add origin https://github.com/shakedr2/salary-tracker.git
git push -u origin main
```

## ✅ פתרון 3: GitHub Desktop

1. פתח GitHub Desktop
2. File → Add Local Repository
3. בחר את התיקייה: `C:\Users\shake\OneDrive\Desktop\קורס דבופס\salary_tracker`
4. Commit את השינויים
5. Publish repository

## 📝 מה יעלה ל-GitHub

### קבצים שיעלו:
- ✅ כל קוד ה-backend (app.py, calculator.py, scraper.py, וכו')
- ✅ כל קוד ה-frontend
- ✅ כל הבדיקות (tests/)
- ✅ תשתית AWS (infra/)
- ✅ הסוכן האוטומטי (agent/)
- ✅ תיעוד (docs/, README.md)
- ✅ CI/CD pipeline (.github/)
- ✅ קבצי תצורה (requirements.txt, Dockerfile, וכו')

### קבצים שלא יעלו (ב-.gitignore):
- ❌ `.env` - משתני סביבה (רגיש!)
- ❌ `venv/` - סביבה וירטואלית
- ❌ `__pycache__/` - קבצי Python
- ❌ `.vscode/` - הגדרות IDE
- ❌ `data/*.json` - נתונים מקומיים

## 🔐 אם יש שגיאת Authentication

אם `git push` נכשל בגלל authentication:

### אפשרות 1: Personal Access Token
1. לך ל-GitHub → Settings → Developer settings → Personal access tokens
2. צור token חדש עם הרשאות `repo`
3. השתמש ב-token במקום סיסמה:
```cmd
git push -u origin main
# Username: shakedr2
# Password: [הדבק את ה-token כאן]
```

### אפשרות 2: SSH
```cmd
git remote set-url origin git@github.com:shakedr2/salary-tracker.git
git push -u origin main
```

## ✅ אחרי ההעלאה

בדוק ב-GitHub:
```
https://github.com/shakedr2/salary-tracker
```

כל הקבצים והשיפורים אמורים להיות שם!

