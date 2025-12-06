#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web scraper למערכת YLM Inspector
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from typing import List
import logging

from .config import Config
from .models import AttendanceRecord

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class YLMScraper:
    """Scraper למערכת YLM"""

    def __init__(self):
        self.config = Config()
        self.driver = None

    def _init_driver(self) -> None:
        """אתחול Chrome WebDriver עם התקנה אוטומטית"""
        options = Options()

        if self.config.SELENIUM_HEADLESS:
            options.add_argument('--headless')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # התקנה אוטומטית של ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

        logger.info("✅ WebDriver initialized with automatic ChromeDriver")

    def _wait_for_element(self, by: By, value: str, timeout: int = None):
        """המתנה לאלמנט"""
        timeout = timeout or self.config.SELENIUM_TIMEOUT
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def login(self) -> bool:
        """התחברות למערכת YLM"""
        try:
            logger.info("🔐 Logging in to YLM...")

            self.driver.get(f"{self.config.YLM_URL}/#/employeeLogin")

            username_field = self._wait_for_element(By.ID, "Username")
            username_field.clear()
            username_field.send_keys(self.config.YLM_USERNAME)

            password_field = self.driver.find_element(By.ID, "YlmCode")
            password_field.clear()
            password_field.send_keys(self.config.YLM_PASSWORD)

            login_btn = WebDriverWait(self.driver, self.config.SELENIUM_TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            login_btn.click()

            WebDriverWait(self.driver, self.config.SELENIUM_TIMEOUT).until(
                EC.url_contains("/menu")
            )

            logger.info("✅ Login successful")
            return True

        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            return False

    def scrape_attendance(self) -> List[AttendanceRecord]:
        """משיכת נתוני נוכחות"""
        try:
            logger.info("📊 Scraping attendance data...")

            url = f"{self.config.YLM_URL}/#/employeeReport?cd={self.config.YLM_USERNAME}"
            self.driver.get(url)

            self._wait_for_element(By.CSS_SELECTOR, "table tbody tr")

            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

            attendance_data = []
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 6:
                        continue

                    day = cells[0].text.strip()
                    date = cells[1].text.strip()
                    site = cells[2].text.strip()
                    entry = cells[3].text.strip().replace(" ", "").replace("", "")
                    exit = cells[4].text.strip().replace(" ", "").replace("", "")
                    total = cells[5].text.strip()

                    if entry and total and ":" in total:
                        record = AttendanceRecord(
                            day=day,
                            date=date,
                            site=site,
                            entry=entry,
                            exit=exit,
                            total_hours=total
                        )
                        attendance_data.append(record)
                        logger.info(f"  📅 {date} ({day}): {entry}→{exit} = {total}")

                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse row: {e}")
                    continue

            logger.info(f"✅ Scraped {len(attendance_data)} records")
            return attendance_data

        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}")
            return []

    def run(self) -> List[AttendanceRecord]:
        """הרצה מלאה"""
        try:
            self._init_driver()

            if not self.login():
                return []

            attendance = self.scrape_attendance()
            return attendance

        except Exception as e:
            logger.error(f"❌ Scraper run failed: {e}")
            return []

        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔒 WebDriver closed")
