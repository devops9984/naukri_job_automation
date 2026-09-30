import time
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    StaleElementReferenceException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager

from answer_engine import AnswerEngine


# ============================================================
# SAFETY SETTINGS
# ============================================================

DRY_RUN = True

ALLOW_FORM_FILL = False
ALLOW_SUBMISSION = False

PAGE_WAIT = 5


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# CREATE BROWSER
# ============================================================

def create_driver():

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
# GET LABEL
# ============================================================

def get_label(driver, element):

    # --------------------------------------------------------
    # 1. LABEL FOR ID
    # --------------------------------------------------------

    try:

        element_id = element.get_attribute("id")

        if element_id:

            labels = driver.find_elements(
                By.TAG_NAME,
                "label"
            )

            for label in labels:

                try:

                    label_for = label.get_attribute(
                        "for"
                    )

                    if label_for == element_id:

                        text = clean_text(
                            label.text
                        )

                        if text:
                            return text

                except Exception:
                    continue

    except Exception:
        pass

    # --------------------------------------------------------
    # 2. ARIA LABEL
    # --------------------------------------------------------

    try:

        value = clean_text(
            element.get_attribute(
                "aria-label"
            )
        )

        if value:
            return value

    except Exception:
        pass

    # --------------------------------------------------------
    # 3. PLACEHOLDER
    # --------------------------------------------------------

    try:

        value = clean_text(
            element.get_attribute(
                "placeholder"
            )
        )

        if value:
            return value

    except Exception:
        pass

    # --------------------------------------------------------
    # 4. NAME
    # --------------------------------------------------------

    try:

        value = clean_text(
            element.get_attribute(
                "name"
            )
        )

        if value:
            return value

    except Exception:
        pass

    # --------------------------------------------------------
    # 5. PARENT TEXT
    # --------------------------------------------------------

    try:

        parent = element.find_element(
            By.XPATH,
            ".."
        )

        value = clean_text(
            parent.text
        )

        if value:

            return value[:300]

    except Exception:
        pass

    return ""


# ============================================================
# FIELD TYPE
# ============================================================

def get_field_type(element):

    tag = (
        element.tag_name
        or ""
    ).lower()

    if tag == "textarea":

        return "TEXTAREA"

    if tag == "select":

        return "SELECT"

    if tag == "input":

        input_type = (
            element.get_attribute("type")
            or "text"
        ).lower()

        if input_type == "email":
            return "EMAIL"

        if input_type == "tel":
            return "PHONE"

        if input_type == "number":
            return "NUMBER"

        if input_type == "radio":
            return "RADIO"

        if input_type == "checkbox":
            return "CHECKBOX"

        if input_type == "file":
            return "FILE"

        return "TEXT"

    return "OTHER"


# ============================================================
# SELECT OPTIONS
# ============================================================

def get_select_options(element):

    options = []

    try:

        option_elements = element.find_elements(
            By.TAG_NAME,
            "option"
        )

        for option in option_elements:

            text = clean_text(
                option.text
            )

            value = option.get_attribute(
                "value"
            )

            if text:

                options.append({
                    "text": text,
                    "value": value
                })

    except Exception:
        pass

    return options


# ============================================================
# RADIO / CHECKBOX OPTIONS
# ============================================================

def get_choice_options(
    driver,
    element
):

    options = []

    try:

        name = (
            element.get_attribute("name")
            or ""
        )

        if name:

            all_elements = driver.find_elements(
                By.CSS_SELECTOR,
                "input[name='" + name + "']"
            )

        else:

            all_elements = [element]

        for item in all_elements:

            value = item.get_attribute(
                "value"
            )

            item_id = item.get_attribute(
                "id"
            )

            label_text = ""

            if item_id:

                labels = driver.find_elements(
                    By.TAG_NAME,
                    "label"
                )

                for label in labels:

                    try:

                        if (
                            label.get_attribute("for")
                            == item_id
                        ):

                            label_text = clean_text(
                                label.text
                            )

                            break

                    except Exception:
                        continue

            if not label_text:

                label_text = value or ""

            options.append({
                "label": label_text,
                "value": value
            })

    except Exception:
        pass

    return options


# ============================================================
# FIND FORM ELEMENTS
# ============================================================

def get_form_elements(driver):

    elements = []

    # INPUTS
    inputs = driver.find_elements(
        By.TAG_NAME,
        "input"
    )

    for element in inputs:

        try:

            input_type = (
                element.get_attribute("type")
                or "text"
            ).lower()

            if input_type in [
                "hidden",
                "submit",
                "button",
                "reset",
                "image"
            ]:

                continue

            elements.append(element)

        except StaleElementReferenceException:

            continue

    # TEXTAREAS
    textareas = driver.find_elements(
        By.TAG_NAME,
        "textarea"
    )

    for element in textareas:

        elements.append(element)

    # SELECTS
    selects = driver.find_elements(
        By.TAG_NAME,
        "select"
    )

    for element in selects:

        elements.append(element)

    return elements


# ============================================================
# ANALYZE FIELD
# ============================================================

def analyze_field(
    driver,
    element,
    answer_engine
):

    try:

        field_type = get_field_type(
            element
        )

        label = get_label(
            driver,
            element
        )

        result = {
            "type": field_type,
            "label": label,
            "answer": None,
            "source": None,
            "status": "REVIEW_REQUIRED",
            "options": []
        }

        # ----------------------------------------------------
        # OPTIONS
        # ----------------------------------------------------

        if field_type == "SELECT":

            result["options"] = (
                get_select_options(
                    element
                )
            )

        elif field_type in [
            "RADIO",
            "CHECKBOX"
        ]:

            result["options"] = (
                get_choice_options(
                    driver,
                    element
                )
            )

        # ----------------------------------------------------
        # ANSWER ENGINE
        # ----------------------------------------------------

        if label:

            answer = answer_engine.get_answer(
                label
            )

            result["answer"] = answer.get(
                "answer"
            )

            result["source"] = answer.get(
                "source"
            )

            result["status"] = answer.get(
                "status"
            )

            if "skill" in answer:

                result["skill"] = answer[
                    "skill"
                ]

        return result

    except StaleElementReferenceException:

        return {
            "type": "STALE",
            "label": "",
            "answer": None,
            "source": None,
            "status": "REVIEW_REQUIRED",
            "options": []
        }


# ============================================================
# PRINT RESULT
# ============================================================

def print_result(
    number,
    result
):

    print()
    print("=" * 70)

    print(
        "FIELD #{}".format(number)
    )

    print(
        "Type     : {}".format(
            result["type"]
        )
    )

    print(
        "Question : {}".format(
            result["label"]
        )
    )

    print(
        "Answer   : {}".format(
            result["answer"]
        )
    )

    print(
        "Source   : {}".format(
            result["source"]
        )
    )

    print(
        "Status   : {}".format(
            result["status"]
        )
    )

    if "skill" in result:

        print(
            "Skill    : {}".format(
                result["skill"]
            )
        )

    if result["options"]:

        print("Options:")

        for option in result["options"]:

            option_label = (
                option.get("label")
                or option.get("text")
                or ""
            )

            option_value = (
                option.get("value")
                or ""
            )

            print(
                "  - {} [{}]".format(
                    option_label,
                    option_value
                )
            )

    print("=" * 70)


# ============================================================
# INSPECT BUTTONS
# ============================================================

def inspect_buttons(driver):

    print()
    print("=" * 70)
    print("BUTTONS")
    print("=" * 70)

    buttons = driver.find_elements(
        By.TAG_NAME,
        "button"
    )

    submit_inputs = driver.find_elements(
        By.CSS_SELECTOR,
        "input[type='submit']"
    )

    buttons = buttons + submit_inputs

    if not buttons:

        print(
            "No buttons found."
        )

        return

    number = 1

    for button in buttons:

        try:

            text = clean_text(
                button.text
            )

            value = clean_text(
                button.get_attribute(
                    "value"
                )
            )

            aria = clean_text(
                button.get_attribute(
                    "aria-label"
                )
            )

            description = (
                text
                or value
                or aria
            )

            if description:

                print(
                    "{}. {}".format(
                        number,
                        description
                    )
                )

                number += 1

        except StaleElementReferenceException:

            continue


# ============================================================
# ANALYZE PAGE
# ============================================================

def analyze_page(
    driver,
    answer_engine
):

    print()
    print("=" * 70)
    print("EXTERNAL APPLICATION FORM")
    print("=" * 70)

    print(
        "URL: {}".format(
            driver.current_url
        )
    )

    print(
        "TITLE: {}".format(
            driver.title
        )
    )

    elements = get_form_elements(
        driver
    )

    print()
    print(
        "FORM ELEMENTS FOUND: {}".format(
            len(elements)
        )
    )

    results = []

    for number, element in enumerate(
        elements,
        start=1
    ):

        result = analyze_field(
            driver,
            element,
            answer_engine
        )

        results.append(
            result
        )

        print_result(
            number,
            result
        )

    inspect_buttons(
        driver
    )

    return results


# ============================================================
# SUMMARY
# ============================================================

def print_summary(results):

    verified = 0
    calculated = 0
    configured = 0
    review = 0

    for result in results:

        status = result.get(
            "status"
        )

        if status == "VERIFIED":

            verified += 1

        elif status == "CALCULATED":

            calculated += 1

        elif status == "CONFIGURED":

            configured += 1

        elif status == "REVIEW_REQUIRED":

            review += 1

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(
        "Total fields       : {}".format(
            len(results)
        )
    )

    print(
        "Verified answers   : {}".format(
            verified
        )
    )

    print(
        "Calculated answers : {}".format(
            calculated
        )
    )

    print(
        "Configured answers : {}".format(
            configured
        )
    )

    print(
        "Review required    : {}".format(
            review
        )
    )

    print()

    print(
        "DRY RUN            : {}".format(
            DRY_RUN
        )
    )

    print(
        "FORM FILL          : {}".format(
            ALLOW_FORM_FILL
        )
    )

    print(
        "SUBMISSION         : {}".format(
            ALLOW_SUBMISSION
        )
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("EXTERNAL FORM ENGINE")
    print("=" * 70)

    print()
    print("DRY RUN MODE")
    print("No fields will be filled.")
    print("No application will be submitted.")
    print()

    url = input(
        "Enter external application URL: "
    ).strip()

    if not url:

        print(
            "No URL supplied."
        )

        return

    answer_engine = AnswerEngine()

    driver = None

    try:

        driver = create_driver()

        print()
        print(
            "Opening URL..."
        )

        driver.get(url)

        time.sleep(
            PAGE_WAIT
        )

        print(
            "Page loaded."
        )

        results = analyze_page(
            driver,
            answer_engine
        )

        print_summary(
            results
        )

        print()
        print("=" * 70)
        print("INSPECTION COMPLETE")
        print("=" * 70)

        print(
            "Browser will remain open."
        )

        print(
            "Press ENTER to close it."
        )

        input()

    except WebDriverException as error:

        print()
        print(
            "BROWSER ERROR:"
        )

        print(error)

    except Exception as error:

        print()
        print(
            "ERROR:"
        )

        print(error)

    finally:

        if driver:

            driver.quit()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()