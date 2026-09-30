import os
import time
import pandas as pd

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

NAUKRI_EMAIL = os.getenv("NAUKRI_EMAIL")
NAUKRI_PASSWORD = os.getenv("NAUKRI_PASSWORD")

TRACKER_FILE = "application_tracker.csv"
OUTPUT_FILE = "external_site_report.csv"

WAIT_TIME = 10


# ============================================================
# DRIVER
# ============================================================

def create_driver():
    options = webdriver.ChromeOptions()

    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    return driver


# ============================================================
# LOGIN
# ============================================================

def login_if_required(driver):

    print("\nChecking Naukri login status...")

    # Check whether already logged in
    try:
        driver.find_element(
            By.CSS_SELECTOR,
            "a.nI-gNb-lg-rg__login"
        )

        print("Login button detected.")
        print("Attempting automated login...")

        login_button = driver.find_element(
            By.CSS_SELECTOR,
            "a.nI-gNb-lg-rg__login"
        )

        driver.execute_script(
            "arguments[0].click();",
            login_button
        )

        time.sleep(2)

    except Exception:
        print("Login button not detected. Session may already be logged in.")

    # Look for login fields
    try:

        email_field = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "input[placeholder='Enter your active Email ID / Username']"
                )
            )
        )

        password_field = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "input[placeholder='Enter your password']"
                )
            )
        )

        print("Login form detected.")

        email_field.clear()
        email_field.send_keys(NAUKRI_EMAIL)

        password_field.clear()
        password_field.send_keys(NAUKRI_PASSWORD)

        login_submit = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.loginButton")
            )
        )

        driver.execute_script(
            "arguments[0].click();",
            login_submit
        )

        time.sleep(5)

        print("Automated login completed.")

    except Exception as e:

        print("Login form not available.")
        print("Continuing with current browser session.")

        return False

    return True


# ============================================================
# GET EXTERNAL LINKS
# ============================================================

def inspect_external_links(driver, job):

    job_id = str(job["job_id"])
    title = str(job["job_title"])
    company = str(job["company"])
    naukri_url = str(job["url"])

    print("\n" + "=" * 80)
    print(f"JOB ID : {job_id}")
    print(f"TITLE  : {title}")
    print(f"COMPANY: {company}")
    print("=" * 80)

    driver.get(naukri_url)

    time.sleep(4)

    current_url = driver.current_url

    print(f"Current URL: {current_url}")

    # --------------------------------------------------------
    # Collect ALL anchors
    # --------------------------------------------------------

    anchors = driver.find_elements(By.TAG_NAME, "a")

    external_links = []
    apply_links = []

    for anchor in anchors:

        try:

            href = anchor.get_attribute("href")
            text = anchor.text.strip()

            aria = anchor.get_attribute("aria-label") or ""
            title_attr = anchor.get_attribute("title") or ""

            combined = (
                f"{text} {aria} {title_attr}"
            ).lower()

            if not href:
                continue

            # Ignore javascript links
            if href.startswith("javascript:"):
                continue

            # External domain
            is_external = (
                "naukri.com" not in href.lower()
            )

            if is_external:

                link_data = {
                    "text": text,
                    "aria": aria,
                    "title": title_attr,
                    "href": href
                }

                external_links.append(link_data)

                # Identify likely application links
                apply_keywords = [
                    "apply",
                    "application",
                    "career",
                    "careers",
                    "job",
                    "workday",
                    "greenhouse",
                    "lever",
                    "smartrecruiters",
                    "successfactors",
                    "icims"
                ]

                if any(
                    keyword in combined or keyword in href.lower()
                    for keyword in apply_keywords
                ):
                    apply_links.append(link_data)

        except Exception:
            continue

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print(f"\nExternal links found: {len(external_links)}")

    for i, link in enumerate(external_links, 1):

        print(f"\nExternal Link #{i}")
        print(f"Text : {link['text']}")
        print(f"ARIA : {link['aria']}")
        print(f"Title: {link['title']}")
        print(f"URL  : {link['href']}")

    print("\n" + "-" * 80)

    print(
        f"Likely application links found: {len(apply_links)}"
    )

    for i, link in enumerate(apply_links, 1):

        print(f"\nAPPLICATION LINK #{i}")
        print(f"Text: {link['text']}")
        print(f"URL : {link['href']}")

    # --------------------------------------------------------
    # Also inspect buttons
    # --------------------------------------------------------

    print("\nInspecting buttons...")

    buttons = driver.find_elements(By.TAG_NAME, "button")

    button_info = []

    for button in buttons:

        try:

            text = button.text.strip()
            aria = button.get_attribute("aria-label") or ""
            title_attr = button.get_attribute("title") or ""
            class_name = button.get_attribute("class") or ""

            combined = (
                f"{text} {aria} {title_attr} {class_name}"
            ).lower()

            if any(
                keyword in combined
                for keyword in [
                    "apply",
                    "application",
                    "career",
                    "external"
                ]
            ):

                info = {
                    "text": text,
                    "aria": aria,
                    "title": title_attr,
                    "class": class_name
                }

                button_info.append(info)

        except Exception:
            continue

    for i, button in enumerate(button_info, 1):

        print(f"\nButton #{i}")
        print(f"Text : {button['text']}")
        print(f"ARIA : {button['aria']}")
        print(f"Title: {button['title']}")
        print(f"Class: {button['class']}")

    # --------------------------------------------------------
    # Save result
    # --------------------------------------------------------

    external_url_list = []

    for link in external_links:

        external_url_list.append(link["href"])

    apply_url_list = []

    for link in apply_links:

        apply_url_list.append(link["href"])

    result = {
        "job_id": job_id,
        "job_title": title,
        "company": company,
        "naukri_url": naukri_url,
        "external_urls": " | ".join(external_url_list),
        "application_urls": " | ".join(apply_url_list),
        "external_link_count": len(external_links),
        "application_link_count": len(apply_links),
        "inspection_status": (
            "APPLICATION LINK FOUND"
            if apply_links
            else "NO APPLICATION LINK FOUND"
        )
    }

    return result


# ============================================================
# LOAD EXTERNAL JOBS
# ============================================================

def load_external_jobs():

    tracker = pd.read_csv(TRACKER_FILE)

    # Only jobs currently marked External Site
    external_jobs = tracker[
        tracker["application_status"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("external site")
    ].copy()

    external_jobs = external_jobs.sort_values(
        by="job_id"
    )

    print("\nExternal jobs found:")
    print(
        external_jobs[
            [
                "job_id",
                "job_title",
                "company"
            ]
        ].to_string(index=False)
    )

    return external_jobs


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("NAUKRI EXTERNAL SITE INSPECTOR")
    print("=" * 80)

    jobs = load_external_jobs()

    if jobs.empty:

        print("\nNo External Site jobs found.")
        return

    print(
        f"\nTotal external jobs to inspect: {len(jobs)}"
    )

    driver = create_driver()

    results = []

    try:

        # ----------------------------------------------------
        # Open Naukri first
        # ----------------------------------------------------

        driver.get("https://www.naukri.com/")

        time.sleep(3)

        login_if_required(driver)

        # ----------------------------------------------------
        # Inspect each job
        # ----------------------------------------------------

        for index, (_, job) in enumerate(
            jobs.iterrows(),
            start=1
        ):

            print(
                f"\n\nPROCESSING {index}/{len(jobs)}"
            )

            try:

                result = inspect_external_links(
                    driver,
                    job
                )

                results.append(result)

            except Exception as e:

                print(
                    f"ERROR inspecting job "
                    f"{job['job_id']}: {e}"
                )

                results.append(
                    {
                        "job_id": job["job_id"],
                        "job_title": job["job_title"],
                        "company": job["company"],
                        "naukri_url": job["url"],
                        "external_urls": "",
                        "application_urls": "",
                        "external_link_count": 0,
                        "application_link_count": 0,
                        "inspection_status": "INSPECTION ERROR"
                    }
                )

            time.sleep(2)

    finally:

        print("\nClosing browser...")

        driver.quit()

    # --------------------------------------------------------
    # Save report
    # --------------------------------------------------------

    report = pd.DataFrame(results)

    report.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 80)
    print("INSPECTION COMPLETE")
    print("=" * 80)

    print(
        f"\nReport saved to: {OUTPUT_FILE}"
    )

    print(
        f"\nJobs inspected: {len(report)}"
    )

    print(
        "\nApplication link status:"
    )

    print(
        report[
            [
                "job_id",
                "company",
                "inspection_status"
            ]
        ].to_string(index=False)
    )

    print("\nNo external website was opened.")
    print("No application was submitted.")
    print("No application form was modified.")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()