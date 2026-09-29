import os
import csv
import time
import logging
from urllib.parse import quote

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

NAUKRI_EMAIL = os.getenv("NAUKRI_EMAIL")
NAUKRI_PASSWORD = os.getenv("NAUKRI_PASSWORD")

JOB_TITLE = "DevOps Engineer"
LOCATION = "Hyderabad"

OUTPUT_FILE = "jobs.csv"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# ============================================================
# CHECK CREDENTIALS
# ============================================================

def validate_credentials():

    if not NAUKRI_EMAIL:
        logger.error("NAUKRI_EMAIL is missing from .env")
        return False

    if not NAUKRI_PASSWORD:
        logger.error("NAUKRI_PASSWORD is missing from .env")
        return False

    logger.info("Naukri credentials loaded.")

    return True


# ============================================================
# START CHROME
# ============================================================

def start_browser():

    logger.info("Starting Chrome...")

    options = webdriver.ChromeOptions()

    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(
            ChromeDriverManager().install()
        ),
        options=options
    )

    return driver


# ============================================================
# LOGIN
# ============================================================

def login_naukri(driver):

    logger.info("Opening Naukri...")

    driver.get(
        "https://www.naukri.com/"
    )

    wait = WebDriverWait(
        driver,
        20
    )

    try:

        # ----------------------------------------------------
        # LOGIN BUTTON
        # ----------------------------------------------------

        logger.info("Looking for Login button...")

        login_button = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//a[contains("
                    "translate(text(),"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                    "'abcdefghijklmnopqrstuvwxyz'),"
                    "'login')]"
                )
            )
        )

        login_button.click()

        logger.info(
            "Login page opened."
        )

        time.sleep(2)

        # ----------------------------------------------------
        # EMAIL
        # ----------------------------------------------------

        logger.info(
            "Entering email..."
        )

        email_field = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//input[contains("
                    "translate(@placeholder,"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                    "'abcdefghijklmnopqrstuvwxyz'),"
                    "'email') "
                    "or contains("
                    "translate(@placeholder,"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                    "'abcdefghijklmnopqrstuvwxyz'),"
                    "'username')]"
                )
            )
        )

        email_field.clear()

        email_field.send_keys(
            NAUKRI_EMAIL
        )

        # ----------------------------------------------------
        # PASSWORD
        # ----------------------------------------------------

        logger.info(
            "Entering password..."
        )

        password_field = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//input[@type='password']"
                )
            )
        )

        password_field.clear()

        password_field.send_keys(
            NAUKRI_PASSWORD
        )

        # ----------------------------------------------------
        # LOGIN BUTTON
        # ----------------------------------------------------

        logger.info(
            "Submitting login..."
        )

        login_submit = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains("
                    "translate(text(),"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                    "'abcdefghijklmnopqrstuvwxyz'),"
                    "'login')]"
                )
            )
        )

        login_submit.click()

        logger.info(
            "Login submitted."
        )

        time.sleep(5)

        logger.info(
            f"Current URL: {driver.current_url}"
        )

        # ----------------------------------------------------
        # BASIC LOGIN CHECK
        # ----------------------------------------------------

        if "mnjuser" in driver.current_url:

            logger.info(
                "Login successful."
            )

            return True

        logger.warning(
            "Login may require additional verification."
        )

        return True

    except Exception as e:

        logger.error(
            f"Login failed: {e}"
        )

        return False


# ============================================================
# OPEN JOB SEARCH
# ============================================================

def open_job_search(driver):

    logger.info(
        f"Preparing search for: {JOB_TITLE}"
    )

    logger.info(
        f"Location: {LOCATION}"
    )

    try:

        # ----------------------------------------------------
        # Build search URL
        # ----------------------------------------------------

        job_slug = JOB_TITLE.lower().replace(
            " ",
            "-"
        )

        location_slug = LOCATION.lower().replace(
            " ",
            "-"
        )

        search_url = (
            f"https://www.naukri.com/"
            f"{job_slug}-jobs-in-"
            f"{location_slug}"
        )

        logger.info(
            f"Search URL: {search_url}"
        )

        driver.get(
            search_url
        )

        time.sleep(7)

        logger.info(
            f"Search page loaded: "
            f"{driver.current_url}"
        )

        return True

    except Exception as e:

        logger.error(
            f"Could not open search page: {e}"
        )

        return False


# ============================================================
# COLLECT JOB CARDS
# ============================================================

def collect_jobs(driver):

    logger.info(
        "Looking for job cards..."
    )

    time.sleep(3)

    jobs = []

    # --------------------------------------------------------
    # Try several possible Naukri card selectors
    # --------------------------------------------------------

    selectors = [

        "//article",

        "//div[contains(@class,'jobTuple')]",

        "//div[contains(@class,'job-tuple')]",

        "//div[contains(@class,'srp-jobtuple')]",

        "//div[contains(@class,'cust-job-tuple')]"

    ]

    job_cards = []

    for selector in selectors:

        try:

            cards = driver.find_elements(
                By.XPATH,
                selector
            )

            if cards:

                job_cards = cards

                logger.info(
                    f"Found {len(cards)} "
                    f"job cards."
                )

                break

        except Exception:

            continue

    # --------------------------------------------------------
    # No cards
    # --------------------------------------------------------

    if not job_cards:

        logger.warning(
            "No job cards detected."
        )

        logger.warning(
            "Naukri's current HTML structure "
            "may be different."
        )

        return jobs

    # --------------------------------------------------------
    # Process cards
    # --------------------------------------------------------

    for index, card in enumerate(
        job_cards,
        start=1
    ):

        try:

            raw_text = card.text.strip()

            if not raw_text:

                continue

            # ------------------------------------------------
            # JOB TITLE
            # ------------------------------------------------

            job_title = ""

            title_selectors = [

                ".//a[contains(@class,'title')]",

                ".//a[contains(@class,'jobTitle')]",

                ".//h2//a",

                ".//h3//a"

            ]

            for selector in title_selectors:

                elements = card.find_elements(
                    By.XPATH,
                    selector
                )

                if elements:

                    job_title = (
                        elements[0]
                        .text
                        .strip()
                    )

                    break

            # ------------------------------------------------
            # COMPANY
            # ------------------------------------------------

            company = ""

            company_selectors = [

                ".//a[contains(@class,'comp-name')]",

                ".//a[contains(@class,'companyName')]",

                ".//span[contains(@class,'comp-name')]"

            ]

            for selector in company_selectors:

                elements = card.find_elements(
                    By.XPATH,
                    selector
                )

                if elements:

                    company = (
                        elements[0]
                        .text
                        .strip()
                    )

                    break

            # ------------------------------------------------
            # URL
            # ------------------------------------------------

            url = ""

            links = card.find_elements(
                By.TAG_NAME,
                "a"
            )

            for link in links:

                href = link.get_attribute(
                    "href"
                )

                if href:

                    if (
                        "naukri.com" in href
                        and (
                            "job" in href.lower()
                            or "jobs" in href.lower()
                        )
                    ):

                        url = href

                        break

            # ------------------------------------------------
            # CREATE RECORD
            # ------------------------------------------------

            job = {

                "job_title": job_title,

                "company": company,

                "location": LOCATION,

                "experience": "",

                "salary": "",

                "url": url,

                "raw_text": raw_text

            }

            jobs.append(
                job
            )

            logger.info(
                f"[{index}] "
                f"{job_title} | "
                f"{company}"
            )

        except Exception as e:

            logger.warning(
                f"Could not process "
                f"job card {index}: {e}"
            )

    logger.info(
        f"Total jobs collected: "
        f"{len(jobs)}"
    )

    return jobs


# ============================================================
# SAVE CSV
# ============================================================

def save_jobs(jobs):

    if not jobs:

        logger.warning(
            "No jobs to save."
        )

        return

    fieldnames = [

        "job_title",

        "company",

        "location",

        "experience",

        "salary",

        "url",

        "raw_text"

    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            jobs
        )

    logger.info(
        f"Saved {len(jobs)} jobs "
        f"to {OUTPUT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    logger.info(
        "======================================"
    )

    logger.info(
        "      NAUKRI JOB AUTOMATION"
    )

    logger.info(
        "======================================"
    )

    # --------------------------------------------------------
    # CHECK CREDENTIALS
    # --------------------------------------------------------

    if not validate_credentials():

        return

    # --------------------------------------------------------
    # START BROWSER
    # --------------------------------------------------------

    driver = start_browser()

    try:

        # ----------------------------------------------------
        # LOGIN
        # ----------------------------------------------------

        login_success = login_naukri(
            driver
        )

        if not login_success:

            logger.error(
                "Login failed."
            )

            return

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        search_success = open_job_search(
            driver
        )

        if not search_success:

            logger.error(
                "Could not open job search."
            )

            return

        # ----------------------------------------------------
        # COLLECT
        # ----------------------------------------------------

        jobs = collect_jobs(
            driver
        )

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        save_jobs(
            jobs
        )

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        print()
        print(
            "======================================"
        )

        print(
            "JOB SEARCH COMPLETED"
        )

        print(
            "======================================"
        )

        print(
            f"Jobs collected : {len(jobs)}"
        )

        print(
            f"CSV file       : {OUTPUT_FILE}"
        )

        print(
            "======================================"
        )

        print()

        # Keep browser open
        input(
            "Press ENTER to close the browser..."
        )

    except Exception as e:

        logger.exception(
            f"Unexpected error: {e}"
        )

        print()
        print(
            "An unexpected error occurred."
        )

        input(
            "Press ENTER to close..."
        )

    finally:

        driver.quit()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()