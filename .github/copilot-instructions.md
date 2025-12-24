# Salary Tracker - AI Agent Instructions

## Project Overview
**YLM Salary Tracker**: A Hebrew-language salary calculator that scrapes attendance data from YLM Inspector (work management system), calculates hourly wages with overtime multipliers, and displays results through a Flask API + vanilla JS frontend.

### Key Architecture
- **Backend**: Flask API (`backend/app.py`) with three core modules
- **Scraper**: Selenium-based web scraper (`backend/scraper.py`) for YLM login and data extraction
- **Calculator**: Salary computation engine (`backend/calculator.py`) with overtime logic
- **Frontend**: Single-page app (`frontend/`) - vanilla JS, RTL Hebrew UI

### Data Flow
```
YLM System → Selenium Scraper → AttendanceRecord[] → SalaryCalculator 
→ SalaryReport → JSON (data/salary_data.json) → Flask API → Frontend UI
```

## Critical Patterns & Conventions

### Language & Locale
- **Primary language**: Hebrew (comments, logs, UI text in Hebrew)
- **Encoding**: UTF-8 with `# -*- coding: utf-8 -*-` at file heads
- **RTL UI**: Frontend uses `<html dir="rtl">` and Hebrew number formatting (`Intl.NumberFormat('he-IL')`)

### Salary Calculation Logic (Complex Business Rules)
Located in `backend/calculator.py`:
- **Regular hours**: First 8 hours/day @ `RATE_REGULAR` (75₪/hour)
- **Overtime 125%**: Hours 8-10/day @ 93.75₪/hour (1.25x rate)
- **Overtime 150%**: Hours 10+/day @ 112.5₪/hour (1.5x rate)
- **Weekend premium**: Friday 17:00 - Saturday 05:00 shifts earn 150% on ALL hours
- **Time parsing**: Custom `_parse_time()` handles "HH:MM" format with space variations

### Data Models (Dataclasses)
Use Python dataclasses (`backend/models.py`):
- `AttendanceRecord`: Raw daily clock-in/out data from scraper
- `DaySalaryBreakdown`: Calculated daily salary with hour breakdowns
- `SalaryReport`: Monthly aggregate with `.to_dict()` for JSON serialization

### Configuration Management
All settings centralized in `backend/config.py`:
- **YLM credentials**: Loaded from `.env` file using `python-dotenv` and `os.getenv()` (never hardcode!)
  - `YLM_USERNAME` and `YLM_PASSWORD` are required; raises `ValueError` if missing
  - Add to root `.env` file: `YLM_USERNAME=your_username` and `YLM_PASSWORD=your_password`
- Salary rates and overtime thresholds
- Weekend/overtime date boundaries (Friday=4, Saturday=5 in 0-indexed weekdays)
- Selenium headless mode, Flask port/debug flags
- File paths use `os.path.join()` for cross-platform compatibility

### API Endpoints
- `GET /` → Serve frontend `index.html`
- `GET /api/salary` → Return cached `salary_data.json`
- `POST /api/refresh` → Scrape YLM + calculate + save (orchestration endpoint)
- `GET /api/health` → Health check
- CORS enabled for frontend requests

### Frontend Conventions
- **Constants**: `API_BASE_URL = 'http://localhost:5000/api'`
- **UI Updates**: Direct DOM manipulation via `getElementById()`
- **Formatting**: `formatNumber()` for currency, `formatDate()` for timestamps
- **Animations**: Floating money emoji effect via CSS animations
- **Error Handling**: Fetch with `.catch()` and user-facing error messages

## Developer Workflows

### Running the Project
```bash
# Start Flask server (run.py serves as entry point)
python run.py
# Server runs on http://localhost:5000
```

### Extending Salary Calculation
1. Modify overtime rates/limits in `backend/config.py` (RATE_*, _LIMIT constants)
2. Update logic in `SalaryCalculator._calculate_daily_breakdown()`
3. Add tests if changing business rules
4. Result serializes via `SalaryReport.to_dict()`

### Web Scraping Issues
- Uses Selenium with `webdriver_manager.chrome.ChromeDriverManager()` for auto driver install
- Headless mode controlled by `Config.SELENIUM_HEADLESS`
- Wait strategies: `WebDriverWait` + explicit element selectors (By.ID, By.CSS_SELECTOR)
- YLM URL: `https://ins.ylm.co.il`
- Login flow: Username field → YLM Code field → Submit button → Redirect to `/menu`

### Common Debugging Points
- **Scraper timeout**: Increase `SELENIUM_TIMEOUT` in config (default 15s)
- **Data not persisting**: Check write permissions on `data/` directory
- **API CORS errors**: Verify `CORS(app)` initialized in `app.py`
- **Frontend stale data**: Manual refresh button makes `POST /api/refresh` call

## Integration Points & Dependencies

### External Services
- **YLM Inspector**: Web-based attendance system (Selenium target)
- **Chrome/Chromium**: Required for Selenium (auto-installed via webdriver_manager)

### Key Imports
- `Flask, CORS` - Web framework
- `Selenium` - Web scraping (webdriver_manager for auto-install)
- `dataclasses` - Data modeling
- `datetime` - Date/time calculations (weekend detection)
- `logging` - Info/error logging to console

### Data Persistence
- Single JSON file: `data/salary_data.json` (created on first `/api/refresh`)
- No database; state is ephemeral except for cached salary report
- Frontend re-requests on page load or user clicks refresh button

## Files & Patterns Quick Reference

| File | Purpose | Key Pattern |
|------|---------|-------------|
| `backend/app.py` | Flask server + endpoints | CORS enabled, error handling with try/except |
| `backend/scraper.py` | YLM data extraction | Selenium WebDriver with headless + explicit waits |
| `backend/calculator.py` | Salary math engine | Dataclass models + complex overtime logic |
| `backend/config.py` | Centralized config | All constants in one class, rates/limits clearly named |
| `frontend/js/app.js` | Frontend logic | Fetch API calls, DOM updates, number formatting |
| `data/salary_data.json` | Cache layer | Human-readable with `ensure_ascii=False` |

## Notes for AI Agents
- **Bilingual comments**: Read Hebrew context in docstrings carefully
- **Credentials management**: Always use `.env` file with `python-dotenv`, never hardcode secrets in config.py
- **Business logic complexity**: Salary calculations depend on multiple date/time boundaries—verify carefully when modifying
- **Testing data**: Use environment variables for credentials; config.py validates required values at startup
- **Frontend-backend sync**: Frontend calls `/api/refresh` asynchronously; loading states may be needed
