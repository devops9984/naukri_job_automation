import os
import time
import pandas as pd

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


load_dotenv()

EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

TRACKER_FILE = "application_tracker.csv"

REVIEW_JOB_IDS = ["001", "002", "007", "009"]


def create_browser():

    options = webdriver.ChromeOptions()

    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    return driver


def login(driver):

    print("\n" + "=" * 70)
    print("LOGIN")
    print("=" * 70)

    current_url = driver.current_url

    # If already logged in, don't do anything
    if "login.naukri.com" not in current_url:

        try:
            login_links = driver.find_elements(
                By.CSS_SELECTOR,
                "a.nI-gNb-lg-rg__login"
            )

            if not login_links:
                print("Login link not found.")
                print("Assuming existing session.")
                return

            login_links[0].click()

        except Exception as e:
            print(f"Could not click login link: {e}")
            return

    try:

        email = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "input[placeholder='Enter your active Email ID / Username']"
                )
            )
        )

        password = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "input[placeholder='Enter your password']"
                )
            )
        )

        email.clear()
        email.send_keys(EMAIL)

        password.clear()
        password.send_keys(PASSWORD)

        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "button.loginButton"
                )
            )
        )

        login_button.click()

        time.sleep(5)

        print("Login completed.")

    except Exception as e:

        print(f"Login inspection error: {e}")


def inspect_page(driver, job_id, title, company, url):

    print("\n")
    print("#" * 80)
    print(f"JOB {job_id}")
    print(f"TITLE   : {title}")
    print(f"COMPANY : {company}")
    print("#" * 80)

    print(f"\nOpening:")
    print(url)

    driver.get(url)

    time.sleep(5)

    print("\nCurrent URL:")
    print(driver.current_url)

    print("\nPage title:")
    print(driver.title)

    # ---------------------------------------------------------
    # BODY TEXT
    # ---------------------------------------------------------

    try:

        body_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        print("\n" + "-" * 70)
        print("IMPORTANT PAGE TEXT")
        print("-" * 70)

        lines = body_text.splitlines()

        keywords = [
            "apply",
            "applied",
            "company site",
            "screening",
            "experience",
            "login",
            "save",
            "submit"
        ]

        found_lines = []

        for line in lines:

            line_clean = line.strip()

            if not line_clean:
                continue

            lower = line_clean.lower()

            if any(keyword in lower for keyword in keywords):

                if line_clean not in found_lines:

                    found_lines.append(line_clean)

        for line in found_lines[:100]:

            print(line)

    except Exception as e:

        print(f"Could not read body text: {e}")

    # ---------------------------------------------------------
    # BUTTONS
    # ---------------------------------------------------------

    print("\n" + "-" * 70)
    print("ALL BUTTONS")
    print("-" * 70)

    buttons = driver.find_elements(By.TAG_NAME, "button")

    if not buttons:

        print("No <button> elements found.")

    else:

        for index, button in enumerate(buttons):

            try:

                text = button.text.strip()

                aria = button.get_attribute("aria-label")

                cls = button.get_attribute("class")

                disabled = button.get_attribute("disabled")

                print(
                    f"[BUTTON {index}] "
                    f"text='{text}' "
                    f"aria='{aria}' "
                    f"disabled='{disabled}'"
                )

                print(
                    f"    class='{cls}'"
                )

            except Exception:
                pass

    # ---------------------------------------------------------
    # LINKS
    # ---------------------------------------------------------

    print("\n" + "-" * 70)
    print("LINKS CONTAINING APPLY / APPLIED")
    print("-" * 70)

    links = driver.find_elements(By.TAG_NAME, "a")

    found_links = 0

    for index, link in enumerate(links):

        try:

            text = link.text.strip()

            href = link.get_attribute("href")

            aria = link.get_attribute("aria-label")

            if (
                "apply" in text.lower()
                or "applied" in text.lower()
                or "apply" in str(aria).lower()
                or "apply" in str(href).lower()
            ):

                print(
                    f"[LINK {index}] "
                    f"text='{text}' "
                    f"aria='{aria}'"
                )

                print(
                    f"    href='{href}'"
                )

                print(
                    f"    class='{link.get_attribute('class')}'"
                )

                found_links += 1

        except Exception:
            pass

    if found_links == 0:

        print("No Apply/Applied links found.")

    # ---------------------------------------------------------
    # ELEMENTS CONTAINING APPLY TEXT
    # ---------------------------------------------------------

    print("\n" + "-" * 70)
    print("ELEMENTS CONTAINING 'APPLY'")
    print("-" * 70)

    elements = driver.find_elements(
        By.XPATH,
        "//*[contains(translate(normalize-space(.), "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
        "'abcdefghijklmnopqrstuvwxyz'), "
        "'apply')]"
    )

    shown = 0

    for element in elements:

        try:

            text = element.text.strip()

            if not text:
                continue

            tag = element.tag_name

            cls = element.get_attribute("class")

            if len(text) <= 150:

                print(
                    f"<{tag}> "
                    f"text='{text}' "
                    f"class='{cls}'"
                )

                shown += 1

                if shown >= 50:
                    break

        except Exception:
            pass

    if shown == 0:

        print("No visible elements containing Apply found.")

    # ---------------------------------------------------------
    # TEXTAREAS
    # ---------------------------------------------------------

    print("\n" + "-" * 70)
    print("TEXTAREAS")
    print("-" * 70)

    textareas = driver.find_elements(
        By.TAG_NAME,
        "textarea"
    )

    if not textareas:

        print("No textarea elements found.")

    else:

        for index, textarea in enumerate(textareas):

            print(
                f"[TEXTAREA {index}] "
                f"placeholder='{textarea.get_attribute('placeholder')}' "
                f"aria='{textarea.get_attribute('aria-label')}' "
                f"class='{textarea.get_attribute('class')}'"
            )

    # ---------------------------------------------------------
    # INPUTS
    # ---------------------------------------------------------

    print("\n" + "-" * 70)
    print("INPUTS")
    print("-" * 70)

    inputs = driver.find_elements(
        By.TAG_NAME,
        "input"
    )

    for index, inp in enumerate(inputs):

        try:

            input_type = inp.get_attribute("type")
            placeholder = inp.get_attribute("placeholder")
            aria = inp.get_attribute("aria-label")
            name = inp.get_attribute("name")
            value = inp.get_attribute("value")

            print(
                f"[INPUT {index}] "
                f"type='{input_type}' "
                f"name='{name}' "
                f"placeholder='{placeholder}' "
                f"aria='{aria}' "
                f"value='{value}'"
            )

        except Exception:
            pass

    print("\n" + "=" * 80)
    print(f"FINISHED INSPECTION FOR JOB {job_id}")
    print("=" * 80)

    input("\nPress ENTER to continue to the next job...")


def main():

    if not EMAIL or not PASSWORD:

        print("ERROR: NAUKRI_EMAIL or NAUKRI_PASSWORD missing from .env")
        return

    if not os.path.exists(TRACKER_FILE):

        print(
            f"ERROR: {TRACKER_FILE} not found."
        )

        return

    df = pd.read_csv(TRACKER_FILE)

    df["job_id"] = (
        df["job_id"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.zfill(3)
    )

    review_jobs = df[
        df["job_id"].isin(REVIEW_JOB_IDS)
    ].copy()

    if review_jobs.empty:

        print("No review-required jobs found.")

        return

    print()
    print("=" * 80)
    print("NAUKRI REVIEW JOB INSPECTOR")
    print("=" * 80)

    print(
        f"Jobs to inspect: {', '.join(REVIEW_JOB_IDS)}"
    )

    driver = create_browser()

    try:

        # Open first job
        first_job = review_jobs.iloc[0]

        driver.get(first_job["url"])

        time.sleep(5)

        login(driver)

        # Inspect all four
        for _, row in review_jobs.iterrows():

            inspect_page(
                driver,
                row["job_id"],
                row["job_title"],
                row["company"],
                row["url"]
            )

    finally:

        print("\nInspection complete.")

        print(
            "Browser will remain open for 20 seconds."
        )

        time.sleep(20)

        driver.quit()


if __name__ == "__main__":
    main()