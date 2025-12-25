// Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Elements
const totalSalaryEl = document.getElementById('totalSalary');
const totalHoursEl = document.getElementById('totalHours');
const regularHoursEl = document.getElementById('regularHours');
const overtimeHoursEl = document.getElementById('overtimeHours');
const breakdownEl = document.getElementById('breakdownit');
const refreshBtn = document.getElementById('refreshBtn');
const lastUpdateEl = document.getElementById('lastUpdate');
const moneyContainer = document.getElementById('moneyContainer');
const loadingSpinner = document.getElementById('loading');
const errorMessage = document.getElementById('errorMessage');

// Show/hide loading spinner
function setLoading(isLoading) {
    if (loadingSpinner) {
        loadingSpinner.style.display = isLoading ? 'block' : 'none';
    }
    if (refreshBtn) {
        refreshBtn.disabled = isLoading;
        refreshBtn.textContent = isLoading ? 'מעדכן...' : 'רענן נתונים';
    }
}

// Show error message
function showError(message) {
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    }
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('he-IL', {
        style: 'currency',
        currency: 'ILS',
        minimumFractionDigits: 2
    }).format(amount);
}

// Load salary data
async function loadSalaryData() {
    try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/salary`);
        
        if (!response.ok) {
            if (response.status === 404) {
                showError('אין נתונים. לחץ על "רענן נתונים" כדי לקבל נתונים חדשים.');
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displaySalaryData(data);
    } catch (error) {
        console.error('Error loading salary data:', error);
        showError('שגיאה בטעינת הנתונים: ' + error.message);
    } finally {
        setLoading(false);
    }
}

// Refresh salary data
async function refreshSalaryData() {
    try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/refresh`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displaySalaryData(data);
    } catch (error) {
        console.error('Error refreshing salary data:', error);
        showError('שגיאה ברענון הנתונים: ' + error.message);
    } finally {
        setLoading(false);
    }
}

// Display salary data
function displaySalaryData(data) {
    if (!data || !data.report) {
        showError('פורמט נתונים שגוי');
        return;
    }
    
    const report = data.report;
    
    // Calculate totals
    const totalSalary = report.total_salary || 0;
    const totalRegular = report.days_breakdown.reduce((sum, d) => sum + (d.regular_hours || 0), 0);
    const totalOT125 = report.days_breakdown.reduce((sum, d) => sum + (d.overtime_125_hours || 0), 0);
    const totalOT150 = report.days_breakdown.reduce((sum, d) => sum + (d.overtime_150_hours || 0), 0);
    const totalHours = totalRegular + totalOT125 + totalOT150;
    
    // Update main display
    if (totalSalaryEl) totalSalaryEl.textContent = formatCurrency(totalSalary);
    if (totalHoursEl) totalHoursEl.textContent = totalHours.toFixed(2);
    if (regularHoursEl) regularHoursEl.textContent = totalRegular.toFixed(2);
    if (overtimeHoursEl) overtimeHoursEl.textContent = (totalOT125 + totalOT150).toFixed(2);
    
    // Update last update time
    if (lastUpdateEl && data.timestamp) {
        const updateTime = new Date(data.timestamp);
        lastUpdateEl.textContent = `עודכן לאחרונה: ${updateTime.toLocaleString('he-IL')}`;
    }
    
    // Display breakdown
    if (breakdownEl) {
        breakdownEl.innerHTML = report.days_breakdown.map(day => `
            <div class="day-card">
                <h3>${day.date}</h3>
                <p>שעות רגילות: ${day.regular_hours.toFixed(2)}</p>
                <p>שעות נוספות 125%: ${day.overtime_125_hours.toFixed(2)}</p>
                <p>שעות נוספות 150%: ${day.overtime_150_hours.toFixed(2)}</p>
                ${day.weekend_premium_applied ? '<p class="weekend-badge">פרמיית סופ"ש ✓</p>' : ''}
                <p class="day-total">סה"כ: ${formatCurrency(day.day_total)}</p>
            </div>
        `).join('');
    }
}

// Initialize
if (refreshBtn) {
    refreshBtn.addEventListener('click', refreshSalaryData);
}

// Load data on page load
loadSalaryData();
