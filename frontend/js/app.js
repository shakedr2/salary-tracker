// קונסטנטות
const API_BASE_URL = 'http://localhost:5000/api';

// אלמנטים
const totalSalaryEl = document.getElementById('totalSalary');
const totalHoursEl = document.getElementById('totalHours');
const regularHoursEl = document.getElementById('regularHours');
const overtimeHoursEl = document.getElementById('overtimeHours');
const breakdownListEl = document.getElementById('breakdownList');
const refreshBtn = document.getElementById('refreshBtn');
const lastUpdateEl = document.getElementById('lastUpdate');
const moneyContainer = document.getElementById('moneyContainer');

// אתחול דולרים מעופפים
function createFloatingMoney() {
    const moneySymbols = ['💵', '💰', '💸', '💴', '💶', '💷'];

    for (let i = 0; i < 15; i++) {
        const money = document.createElement('div');
        money.className = 'money';
        money.textContent = moneySymbols[Math.floor(Math.random() * moneySymbols.length)];
        money.style.left = `${Math.random() * 100}%`;
        money.style.top = `${Math.random() * 100}%`;
        money.style.animationDelay = `${Math.random() * 4}s`;
        money.style.animationDuration = `${4 + Math.random() * 2}s`;
        moneyContainer.appendChild(money);
    }
}

// פורמט מספרים
function formatNumber(num) {
    return new Intl.NumberFormat('he-IL', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(num);
}

// פורמט תאריך
function formatDate(isoString) {
    const date = new Date(isoString);
    return new Intl.DateTimeFormat('he-IL', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// עדכון UI
function updateUI(data) {
    // עדכון סכום ראשי
    const amountEl = totalSalaryEl.querySelector('.amount');
    amountEl.textContent = formatNumber(data.total_salary);

    // אנימציית ספירה
    animateValue(amountEl, 0, data.total_salary, 1500);

    // עדכון סטטיסטיקות
    totalHoursEl.textContent = formatNumber(data.total_hours);
    regularHoursEl.textContent = formatNumber(data.regular_hours);
    overtimeHoursEl.textContent = formatNumber(data.overtime_125_hours + data.overtime_150_hours);

    // עדכון פירוט יומי
    breakdownListEl.innerHTML = '';

    if (data.breakdown && data.breakdown.length > 0) {
        data.breakdown.forEach(day => {
            const item = document.createElement('div');
            item.className = `breakdown-item ${day.is_weekend ? 'weekend' : ''}`;

            item.innerHTML = `
                <div>
                    <div class="breakdown-date">${day.date} (${day.day}) ${day.is_weekend ? '🎉' : ''}</div>
                    <div class="breakdown-details">${day.site} • ${day.entry} - ${day.exit} • ${formatNumber(day.hours)} שעות</div>
                </div>
                <div class="breakdown-salary">₪${formatNumber(day.salary)}</div>
            `;

            breakdownListEl.appendChild(item);
        });
    } else {
        breakdownListEl.innerHTML = '<div class="loading">אין נתונים זמינים</div>';
    }

    // עדכון זמן עדכון אחרון
    lastUpdateEl.textContent = formatDate(data.timestamp);
}

// אנימציית ספירה
function animateValue(element, start, end, duration) {
    const startTime = performance.now();

    function updateValue(currentTime) {
        const elapsedTime = currentTime - startTime;
        const progress = Math.min(elapsedTime / duration, 1);

        const currentValue = start + (end - start) * easeOutQuad(progress);
        element.textContent = formatNumber(currentValue);

        if (progress < 1) {
            requestAnimationFrame(updateValue);
        }
    }

    requestAnimationFrame(updateValue);
}

// פונקציית easing
function easeOutQuad(t) {
    return t * (2 - t);
}

// טעינת נתונים
async function loadSalaryData() {
    try {
        const response = await fetch(`${API_BASE_URL}/salary`);

        if (!response.ok) {
            throw new Error('Failed to load data');
        }

        const data = await response.json();
        updateUI(data);

    } catch (error) {
        console.error('Error loading salary data:', error);
        breakdownListEl.innerHTML = `
            <div class="loading" style="color: #e74c3c;">
                שגיאה בטעינת נתונים. אנא לחץ על "רענן נתונים".
            </div>
        `;
    }
}

// רענון נתונים
async function refreshData() {
    refreshBtn.disabled = true;
    refreshBtn.textContent = '⏳ מעדכן נתונים...';

    try {
        const response = await fetch(`${API_BASE_URL}/refresh`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Failed to refresh data');
        }

        const data = await response.json();
        updateUI(data);

        // הודעת הצלחה
        showNotification('✅ הנתונים עודכנו בהצלחה!', 'success');

    } catch (error) {
        console.error('Error refreshing data:', error);
        showNotification('❌ שגיאה בעדכון הנתונים', 'error');
    } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = '🔄 רענן נתונים';
    }
}

// הצגת הודעה
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#27ae60' : '#e74c3c'};
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        z-index: 1000;
        animation: slideInRight 0.3s ease-out;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Event listeners
refreshBtn.addEventListener('click', refreshData);

// אתחול
document.addEventListener('DOMContentLoaded', () => {
    createFloatingMoney();
    loadSalaryData();
});

// רענון אוטומטי כל 5 דקות
setInterval(loadSalaryData, 5 * 60 * 1000);
