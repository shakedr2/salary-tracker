# 🤖 Automated Agent - Salary Tracker

סוכן אוטומטי לבדיקה, ניטור ושיפור התוכנה

## 📋 תכונות

### ✅ בדיקות אוטומטיות
- **בדיקת תחביר Python** - בודק שגיאות תחביר
- **בדיקת imports** - מוודא שכל ה-imports תקינים
- **בדיקת אבטחה** - מחפש credentials קשיחים בקוד
- **בדיקת תלויות** - מוודא שכל החבילות מותקנות
- **הרצת בדיקות** - מריץ את כל ה-tests

### ☁️ ניטור AWS
- **מצב EC2 instances** - בודק אם ה-instances רצים
- **Security Groups** - בודק הגדרות אבטחה
- **CloudWatch Metrics** - ניטור CPU, Memory, וכו'
- **Health Checks** - בדיקת בריאות האפליקציה

### 🔧 שיפורים אוטומטיים
- **הצעות שיפור** - רשימת שיפורים מומלצים
- **דוחות מפורטים** - דוחות JSON עם כל הממצאים

## 🚀 שימוש

### הרצה מקומית

```bash
# התקנת תלויות
pip install -r agent/requirements.txt

# הרצת הסוכן
python agent/main_agent.py
```

הסוכן יבצע:
1. בדיקות איכות קוד
2. בדיקות תשתית AWS
3. יצירת דוח מפורט ב-`agent/report.json`
4. הצעות שיפור

### דוגמת פלט

```
============================================================
Starting Automated Quality Checks
============================================================

[1/6] Code Quality Checks
Checking Python syntax...
Checking imports...
Checking security issues...
Checking requirements...

[2/6] Running Tests
Running tests...

[3/6] AWS Infrastructure Checks
Checking EC2 instances...
Checking Security Groups...

[4/6] Generating Improvement Suggestions

[5/6] Generating Summary
============================================================
Summary:
  Checks Passed: 5/5
  Issues Found: 0
  Improvements Suggested: 8
============================================================
```

## 📊 דוח

הסוכן יוצר דוח JSON ב-`agent/report.json` עם:
- תוצאות כל הבדיקות
- רשימת בעיות שנמצאו
- הצעות שיפור
- מצב תשתית AWS

## ☁️ AWS Lambda Integration

הסוכן כולל פונקציית Lambda לניטור אוטומטי:

### הגדרה

1. **צור Lambda function:**
```bash
cd agent
zip lambda_monitor.zip lambda_monitor.py
```

2. **Deploy עם Terraform:**
```bash
cd infra
terraform apply
```

3. **הגדר SNS Topic** (אופציונלי) לקבלת התראות

### Lambda Features

- **ניטור אוטומטי** כל 5 דקות
- **CloudWatch Alarms** - התראות על CPU גבוה
- **Health Checks** - בדיקת בריאות האפליקציה
- **SNS Alerts** - שליחת התראות

## 🔧 שיפורי תשתית

הסוכן מציע שיפורים אוטומטיים:

### שיפורים מומלצים:
1. ✅ הוספת CloudWatch alarms ל-CPU ו-Memory
2. ✅ הפעלת CloudWatch Logs ללוגים
3. ✅ הוספת Auto Scaling Group לזמינות גבוהה
4. ✅ שימוש ב-Application Load Balancer
5. ✅ הוספת S3 bucket לגיבויים
6. ✅ CloudWatch metrics לבריאות האפליקציה
7. ✅ Lambda function לגיבויים אוטומטיים
8. ✅ Systems Manager לגישה מאובטחת

## 📝 קבצים

```
agent/
├── main_agent.py          # סוכן ראשי
├── lambda_monitor.py      # Lambda function לניטור
├── deploy.sh              # סקריפט deployment
├── requirements.txt       # תלויות
├── README.md              # מדריך זה
└── report.json            # דוח (נוצר אוטומטית)
```

## 🛠️ Deployment אוטומטי

השתמש ב-`deploy.sh` לפריסה מלאה:

```bash
chmod +x agent/deploy.sh
./agent/deploy.sh
```

הסקריפט מבצע:
1. בדיקות איכות
2. בניית Docker image
3. הרצת tests
4. פריסת תשתית AWS
5. פריסת האפליקציה ל-EC2

## 📈 CloudWatch Integration

לאחר הפריסה, CloudWatch ינטר:
- **CPU Utilization** - התראה ב-80%
- **Instance Status** - בדיקת מצב ה-instance
- **Application Health** - בדיקת בריאות האפליקציה

## 🔐 אבטחה

הסוכן בודק:
- ✅ אין credentials קשיחים בקוד
- ✅ Security Groups מוגדרים נכון
- ✅ SSH access מוגבל
- ✅ Environment variables משמשים ל-secrets

## 📞 תמיכה

לשאלות או בעיות, בדוק את:
- `agent/report.json` - דוח מפורט
- `agent/agent.log` - לוגים
- CloudWatch Logs - לוגים מ-AWS

## 🎯 Roadmap

- [ ] שיפורים אוטומטיים בקוד
- [ ] אינטגרציה עם GitHub Actions
- [ ] בדיקות ביצועים אוטומטיות
- [ ] דוחות ויזואליים
- [ ] Slack/Discord notifications

