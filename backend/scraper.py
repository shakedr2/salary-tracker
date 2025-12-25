# -*- coding: utf-8 -*-
"""
Improved Selenium-based scraper for YLM (backend.scraper).

Features:
- Retry mechanism with backoff
- Robust error handling and logging
- Ensures driver is closed in finally
- Flexible parsing of attendance cells (multiple periods, cross-midnight)
- Marks periods that overlap the weekend premium window (Friday 17:00 - Sunday 05:00)
- Returns list of attendance records as dicts:
    {"date": "YYYY-MM-DD", "periods": [("HH:MM","HH:MM"), ...], "raw": {...}}
"""
from __future__ import annotations
import logging
import re
import time
from typing import List, Tuple, Any, Dict, Optional
from datetime import datetime, date, time as dt_time, timedelta

from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options

from .config import (
    SELENIUM_HEADLESS,
    SELENIUM_TIMEOUT,
    SCRAPER_RETRIES,
    SCRAPER_RETRY_BACKOFF,
    WEEKEND_PREMIUM_START,
    WEEKEND_PREMIUM_END,
    get_credentials,
)

logger = logging.getLogger("backend.scraper")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class ScraperError(Exception):
    pass


_TIME_RE = re.compile(r"(\d{1,2}:\d{2})")


def _new_driver() -> webdriver.Chrome:
    options = Options()
    if SELENIUM_HEADLESS:
        # Modern headless flag; fall back to --headless if needed
        try:
            options.add_argument("--headless=new")
        except Exception:
            options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=he-IL")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(SELENIUM_TIMEOUT)
    return driver


def _parse_time_strings_from_text(text: str) -> List[str]:
    """Return all HH:MM-like substrings found in text."""
    if not text:
        return []
    return _TIME_RE.findall(text)


def _normalize_periods_from_row(date_cell_text: str, *period_texts: str) -> List[Tuple[str, str]]:
    """
    Given a date cell and one or more texts that may contain time ranges,
    return a list of (start_str, end_str) tuples in 'HH:MM' format.

    Handles:
    - single pair like "09:00 - 17:00"
    - compact pair like "09:00/17:00"
    - multiple pairs separated by commas/newlines
    - case where only two times appear -> treat as single period
    - edge cases: odd number of times -> ignore dangling time
    - cross-midnight is allowed (start > end).
    """
    combined = " ".join([t or "" for t in period_texts]).strip()
    if not combined:
        return []

    # Split by common separators that separate periods
    parts = re.split(r"[,\n;|/]+", combined)
    periods: List[Tuple[str, str]] = []
    for p in parts:
        times = _parse_time_strings_from_text(p)
        if len(times) >= 2:
            # Pair the first two times (ignore extras in this segment)
            start, end = times[0], times[1]
            periods.append((start, end))
        elif len(times) == 1:
            # Single time only - cannot infer end -> skip
            continue
        else:
            # Fallback: try to find pattern like HH:MM-HH:MM with dash
            m = re.search(r"(\d{1,2}:\d{2})\s*[-–—]\s*(\d{1,2}:\d{2})", p)
            if m:
                periods.append((m.group(1), m.group(2)))
    return periods


def _parse_date_cell(text: str) -> Optional[date]:
    """
    Try parse date from a table cell text.
    Accepts ISO-style, dd/mm/YYYY, and single-day numbers (1-31) - the latter requires context and will return None.
    """
    text = (text or "").strip()
    if not text:
        return None
    # Try ISO YYYY-MM-DD
    try:
        dt = datetime.fromisoformat(text)
        return dt.date()
    except Exception:
        pass
    # Try dd/mm/YYYY or dd/mm/YY
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except Exception:
            continue
    # Try single day number (1-31) - ambiguous: return None here so caller may infer month
    if re.fullmatch(r"\d{1,2}", text):
        return None
    return None


def _period_overlaps_weekend_premium(rec_date: date, start_str: str, end_str: str) -> bool:
    """
    Determine whether the period overlaps the configured weekend premium window.

    WEEKEND_PREMIUM_START and WEEKEND_PREMIUM_END are dicts from config:
      e.g. {"weekday": 4, "hour": 17, "minute": 0}  # Friday 17:00
            {"weekday": 6, "hour": 5, "minute": 0}   # Sunday 05:00

    Logic:
    - Compute the most recent start-window anchor (the Friday corresponding to or before rec_date)
    - Build start_window (Friday 17:00) and end_window (Sunday 05:00)
    - Convert the period to absolute datetimes (taking cross-midnight into account)
    - Check for overlap
    """
    try:
        start_cfg = WEEKEND_PREMIUM_START
        end_cfg = WEEKEND_PREMIUM_END
        start_weekday = start_cfg.get("weekday", 4)  # Friday (4)
        start_hour = start_cfg.get("hour", 17)
        start_min = start_cfg.get("minute", 0)
        end_weekday = end_cfg.get("weekday", 6)      # Sunday (6)
        end_hour = end_cfg.get("hour", 5)
        end_min = end_cfg.get("minute", 0)

        # find the date of the most recent 'start_weekday' relative to rec_date
        days_since_start = (rec_date.weekday() - start_weekday) % 7
        start_anchor = rec_date - timedelta(days=days_since_start)
        start_window = datetime.combine(start_anchor, dt_time(start_hour, start_min))

        # compute end window by adding appropriate days
        days_until_end = (end_weekday - start_weekday) % 7
        end_anchor = start_anchor + timedelta(days=days_until_end)
        end_window = datetime.combine(end_anchor, dt_time(end_hour, end_min))

        # parse start and end times to datetimes relative to rec_date
        def to_dt(d: date, tstr: str) -> datetime:
            hh, mm = map(int, tstr.split(":"))
            dtobj = datetime.combine(d, dt_time(hh, mm))
            return dtobj

        # Determine period start/end datetimes. If end <= start, assume cross-midnight and add one day to end.
        period_start = to_dt(rec_date, start_str)
        period_end = to_dt(rec_date, end_str)
        if period_end <= period_start:
            period_end += timedelta(days=1)

        # Now check overlap between [period_start, period_end) and [start_window, end_window)
        overlap = (period_start < end_window) and (period_end > start_window)
        return overlap
    except Exception:
        return False


def _row_to_record(row, month_hint: Optional[int] = None, year_hint: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Convert a selenium row element to an attendance record dict.
    Tries multiple strategies for extracting date and periods.
    month_hint/year_hint can be provided if table only has day-of-month numbers.
    """
    try:
        cols = row.find_elements(By.TAG_NAME, "td")
        if not cols:
            return None

        # Try to identify typical columns: date, in, out, maybe notes
        # Heuristic: first column is date, the next two are in/out or times
        date_text = cols[0].text.strip()
        date_parsed = _parse_date_cell(date_text)

        # if date_parsed is None but month_hint/year_hint provided and date_text is day number -> construct date
        if date_parsed is None and month_hint and year_hint and re.fullmatch(r"\d{1,2}", date_text):
            daynum = int(date_text)
            try:
                date_parsed = date(year_hint, month_hint, daynum)
            except Exception:
                date_parsed = None

        # Collect period texts from likely columns
        period_texts = []
        if len(cols) >= 3:
            # treat cols[1], cols[2] as in/out or period info
            period_texts.append(cols[1].text.strip())
            period_texts.append(cols[2].text.strip())
            # also consider an optional 4th column as additional period data
            if len(cols) >= 4:
                period_texts.append(cols[3].text.strip())
        else:
            # fallback: take entire row text
            period_texts.append(row.text)

        periods = _normalize_periods_from_row(date_text, *period_texts)

        # If no explicit periods but there are times in row text, try to pair them
        if not periods:
            times = _parse_time_strings_from_text(" ".join(period_texts))
            if len(times) >= 2:
                # pair sequentially
                paired = []
                for i in range(0, len(times) - 1, 2):
                    paired.append((times[i], times[i + 1]))
                periods = paired

        # Build record
        rec_date_str = date_parsed.isoformat() if date_parsed else date_text
        raw = {
            "date_cell": date_text,
            "period_cells": period_texts,
            "row_text": row.text,
        }
        record = {"date": rec_date_str, "periods": periods, "raw": raw}

        # annotate periods with weekend flag if any period overlaps
        weekend_flag = False
        if date_parsed:
            for s, e in periods:
                if _period_overlaps_weekend_premium(date_parsed, s, e):
                    weekend_flag = True
                    break
        record["weekend_premium"] = weekend_flag
        return record

    except Exception as ex:
        logger.debug("Failed to convert row to record: %s", ex)
        return None


def _scrape_once(target_year: int, target_month: int) -> List[Dict[str, Any]]:
    """
    One attempt to scrape the target month. Returns list of attendance record dicts.
    """
    username, password = get_credentials()
    driver = None
    try:
        driver = _new_driver()
        wait = WebDriverWait(driver, SELENIUM_TIMEOUT)
        base_url = "https://ins.ylm.co.il"
        logger.info("Opening %s", base_url)
        driver.get(base_url)

        # --- LOGIN flow (may need adjustment to actual site DOM) ---
        try:
            username_el = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            username_el.clear()
            username_el.send_keys(username)
        except TimeoutException:
            try:
                username_el = driver.find_element(By.ID, "username")
                username_el.clear()
                username_el.send_keys(username)
            except Exception as ex:
                raise ScraperError(f"Username field not found: {ex}")

        try:
            password_el = driver.find_element(By.NAME, "password")
            password_el.clear()
            password_el.send_keys(password)
        except NoSuchElementException:
            try:
                password_el = driver.find_element(By.ID, "password")
                password_el.clear()
                password_el.send_keys(password)
            except Exception as ex:
                raise ScraperError(f"Password field not found: {ex}")

        # Submit login if possible
        try:
            submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            submit.click()
        except Exception:
            # ignore, maybe login auto-submits
            pass

        # Wait for dashboard/menu - tolerant
        try:
            wait.until(EC.url_contains("/menu"))
        except TimeoutException:
            logger.info("Menu URL not detected - continuing anyway")

        # Navigate to the attendance page - site-specific: try common patterns
        attendance_urls = [
            "/attendance",
            "/attendance/list",
            "/presence",
            "/inspector/attendance",
            "/time-attendance",
        ]
        attendance_page_loaded = False
        for suffix in attendance_urls:
            try:
                driver.get(base_url + suffix)
                time.sleep(0.5)
                if "attendance" in driver.current_url or "presence" in driver.current_url:
                    attendance_page_loaded = True
                    break
            except Exception:
                continue

        # If not loaded by heuristics, assume current page contains the table
        # Try to find table rows
        rows = []
        try:
            # Prefer semantic rows if available
            rows = driver.find_elements(By.CSS_SELECTOR, "tr.attendance-row")
        except Exception:
            rows = []

        if not rows:
            # fallback to any table rows in a main content area
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
            except Exception:
                rows = []

        records: List[Dict[str, Any]] = []
        for row in rows:
            rec = _row_to_record(row, month_hint=target_month, year_hint=target_year)
            if rec:
                records.append(rec)

        logger.info("Scraped %d records for %04d-%02d", len(records), target_year, target_month)
        return records

    except WebDriverException as e:
        logger.exception("WebDriverException during scraping: %s", e)
        raise ScraperError(str(e))
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as ex:
                logger.debug("Error quitting driver: %s", ex)


def scrape_month(year: int, month: int) -> List[Dict[str, Any]]:
    """
    Public entry with retry/backoff. Returns attendance records or raises ScraperError.
    """
    attempt = 0
    backoff = 1.0
    last_exc: Optional[Exception] = None
    while attempt < max(1, SCRAPER_RETRIES):
        attempt += 1
        try:
            logger.info("Scrape attempt %d for %04d-%02d", attempt, year, month)
            return _scrape_once(year, month)
        except ScraperError as e:
            last_exc = e
            logger.warning("Attempt %d failed: %s", attempt, e)
            if attempt >= SCRAPER_RETRIES:
                logger.error("All scrape attempts failed.")
                raise
            sleep_for = backoff * SCRAPER_RETRY_BACKOFF
            logger.info("Waiting %.1f seconds before retry...", sleep_for)
            time.sleep(sleep_for)
            backoff *= 2
        except Exception as e:
            last_exc = e
            logger.exception("Unexpected error during scraping: %s", e)
            if attempt >= SCRAPER_RETRIES:
                raise ScraperError(f"Unexpected error after {attempt} attempts: {e}") from e
            time.sleep(backoff)
            backoff *= SCRAPER_RETRY_BACKOFF
    # Should not reach here
    raise ScraperError("Scraping failed (unexpected exit)")
