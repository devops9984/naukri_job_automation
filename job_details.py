import csv
import time
import logging

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "jobs.csv"
OUTPUT_FILE = "job_details.csv"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# ============================================================
# START BROWSER
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
# READ jobs.csv
# ============================================================

def read_jobs():

    logger.info(
        f"Reading {INPUT_FILE}..."
    )

    jobs = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            url = row.get(
                "url",
                ""
            ).strip()

            if not url:

                logger.warning(
                    f"Skipping job without URL: "
                    f"{row.get('job_title', '')}"
                )

                continue

            jobs.append(row)

    logger.info(
        f"Found {len(jobs)} jobs with URLs."
    )

    return jobs


# ============================================================
# EXTRACT FULL JOB DESCRIPTION
# ============================================================

def extract_job_description(driver):

    wait = WebDriverWait(
        driver,
        15
    )

    # --------------------------------------------------------
    # Give page time to load
    # --------------------------------------------------------

    time.sleep(3)

    # --------------------------------------------------------
    # Possible JD containers
    # --------------------------------------------------------

    selectors = [

        "//div[contains(@class,'styles_JDC__')]",

        "//div[contains(@class,'job-desc')]",

        "//div[contains(@class,'jobDescription')]",

        "//section[contains(@class,'job-desc')]",

        "//div[contains(@class,'dang-inner-html')]"

    ]

    for selector in selectors:

        try:

            elements = driver.find_elements(
                By.XPATH,
                selector
            )

            for element in elements:

                text = element.text.strip()

                if len(text) > 100:

                    return text

        except Exception:

            continue

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    logger.warning(
        "Specific JD container not found."
    )

    # Search page for common JD headings
    try:

        body = wait.until(
            EC.presence_of_element_located(
                (
                    By.TAG_NAME,
                    "body"
                )
            )
        )

        text = body.text.strip()

        return text

    except Exception:

        return ""


# ============================================================
# PROCESS JOBS
# ============================================================

def collect_job_details(
    driver,
    jobs
):

    results = []

    total = len(jobs)

    for index, job in enumerate(
        jobs,
        start=1
    ):

        title = job.get(
            "job_title",
            ""
        )

        company = job.get(
            "company",
            ""
        )

        url = job.get(
            "url",
            ""
        )

        logger.info(
            f"[{index}/{total}] "
            f"{title} | {company}"
        )

        logger.info(
            f"Opening: {url}"
        )

        try:

            driver.get(url)

            description = (
                extract_job_description(
                    driver
                )
            )

            if description:

                logger.info(
                    f"JD extracted: "
                    f"{len(description)} characters"
                )

            else:

                logger.warning(
                    "No JD extracted."
                )

            result = {

                "job_title": title,

                "company": company,

                "location": job.get(
                    "location",
                    ""
                ),

                "experience": job.get(
                    "experience",
                    ""
                ),

                "salary": job.get(
                    "salary",
                    ""
                ),

                "url": url,

                "full_job_description":
                    description

            }

            results.append(
                result
            )

        except Exception as e:

            logger.error(
                f"Failed to process job: {e}"
            )

            results.append(
                {
                    "job_title": title,
                    "company": company,
                    "location": job.get(
                        "location",
                        ""
                    ),
                    "experience": job.get(
                        "experience",
                        ""
                    ),
                    "salary": job.get(
                        "salary",
                        ""
                    ),
                    "url": url,
                    "full_job_description": ""
                }
            )

        # ----------------------------------------------------
        # Small delay between jobs
        # ----------------------------------------------------

        time.sleep(2)

    return results


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(results):

    if not results:

        logger.warning(
            "Nothing to save."
        )

        return

    fieldnames = [

        "job_title",

        "company",

        "location",

        "experience",

        "salary",

        "url",

        "full_job_description"

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
            results
        )

    logger.info(
        f"Saved {len(results)} jobs "
        f"to {OUTPUT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("             FULL JD COLLECTOR")
    print("=" * 70)

    jobs = read_jobs()

    if not jobs:

        print(
            "No jobs found in jobs.csv"
        )

        return

    driver = start_browser()

    try:

        results = collect_job_details(
            driver,
            jobs
        )

        save_results(
            results
        )

        print()
        print("=" * 70)
        print("             JD COLLECTION COMPLETE")
        print("=" * 70)

        print(
            f"Jobs processed : {len(results)}"
        )

        print(
            f"Output file    : {OUTPUT_FILE}"
        )

        print("=" * 70)

        input(
            "\nPress ENTER to close browser..."
        )

    except Exception as e:

        logger.exception(
            f"Unexpected error: {e}"
        )

        input(
            "\nPress ENTER to close..."
        )

    finally:

        driver.quit()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()