import os
import re
import time
import pandas as pd

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
    TimeoutException,
)


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

NAUKRI_EMAIL = os.getenv("NAUKRI_EMAIL")
NAUKRI_PASSWORD = os.getenv("NAUKRI_PASSWORD")

TRACKER_FILE = "application_tracker.csv"
SELECTED_JOBS_FILE = "selected_jobs.csv"
ANSWERS_FILE = "application_answers.csv"

START_JOB_ID = 1
END_JOB_ID = 20

MAX_SCREENING_QUESTIONS = 10

WAIT_BETWEEN_JOBS = 3

ALLOW_FINAL_SUBMISSION = False


# ============================================================
# VERIFIED PROFILE FACTS
# ============================================================

PROFILE_FACTS = {
    "llm_experience_years": "2",
    "healthcare_experience": "Yes",

    "llmops_experience_years": None,
    "aws_experience_years": None,
    "gcp_experience_years": None,
    "azure_experience_years": None,
    "python_experience_years": None,
    "docker_experience_years": None,
    "kubernetes_experience_years": None,
    "devops_experience_years": None,
}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def normalize_dataframe_columns(df):

    df = df.copy()

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    return df


def find_column(df, possible_names):

    normalized = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    for name in possible_names:

        key = str(name).strip().lower()

        if key in normalized:
            return normalized[key]

    return None


def normalize_job_id(value):

    if pd.isna(value):
        return ""

    value = str(value).strip()

    if value.endswith(".0"):
        value = value[:-2]

    digits = re.sub(r"\D", "", value)

    if not digits:
        return ""

    return digits.zfill(3)


def clean_text(value):

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    return str(value).strip()


# ============================================================
# ANSWER DATABASE
# ============================================================

class AnswerDatabase:

    def __init__(self, filepath):

        self.answers = {}

        if not os.path.exists(filepath):

            print(
                f"Answer database not found: {filepath}"
            )

            return

        try:

            df = pd.read_csv(filepath)

            df = normalize_dataframe_columns(df)

            question_column = find_column(
                df,
                [
                    "question_pattern",
                    "question",
                    "pattern"
                ]
            )

            answer_column = find_column(
                df,
                [
                    "answer",
                    "response"
                ]
            )

            if not question_column or not answer_column:

                print(
                    "Answer database columns not recognized."
                )

                return

            for _, row in df.iterrows():

                question = clean_text(
                    row[question_column]
                )

                answer = clean_text(
                    row[answer_column]
                )

                if question and answer:

                    self.answers[
                        self.normalize(question)
                    ] = answer

            print(
                f"Answer database loaded: {len(self.answers)}"
            )

        except Exception as e:

            print(
                f"Could not load answer database: {e}"
            )


    @staticmethod
    def normalize(text):

        text = clean_text(text).lower()

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()


    def find_answer(self, question):

        normalized_question = self.normalize(
            question
        )

        if not normalized_question:
            return None

        # Exact match
        if normalized_question in self.answers:

            return self.answers[
                normalized_question
            ]

        # Substring matching
        for stored_question, answer in self.answers.items():

            if (
                stored_question in normalized_question
                or normalized_question in stored_question
            ):

                return answer

        return None


# ============================================================
# PROFILE ANSWER ENGINE
# ============================================================

class ProfileAnswerEngine:

    def __init__(self, answer_database):

        self.answer_database = answer_database


    def get_answer(self, question):

        question_clean = clean_text(question)

        normalized = question_clean.lower()

        # ----------------------------------------------------
        # First use explicit answer database
        # ----------------------------------------------------

        database_answer = self.answer_database.find_answer(
            question_clean
        )

        if database_answer is not None:

            return database_answer


        # ----------------------------------------------------
        # Healthcare experience
        # ----------------------------------------------------

        if (
            "healthcare" in normalized
            and (
                "experience" in normalized
                or "worked" in normalized
                or "domain" in normalized
            )
        ):

            return PROFILE_FACTS[
                "healthcare_experience"
            ]


        # ----------------------------------------------------
        # LLM experience
        # ----------------------------------------------------

        if (
            "llm" in normalized
            and "llmops" not in normalized
            and (
                "experience" in normalized
                or "years" in normalized
            )
        ):

            return PROFILE_FACTS[
                "llm_experience_years"
            ]


        # ----------------------------------------------------
        # DO NOT assume LLMOps = LLM
        # ----------------------------------------------------

        if "llmops" in normalized:

            return PROFILE_FACTS[
                "llmops_experience_years"
            ]


        # ----------------------------------------------------
        # GCP
        # ----------------------------------------------------

        if (
            "gcp" in normalized
            and (
                "experience" in normalized
                or "years" in normalized
            )
        ):

            return PROFILE_FACTS[
                "gcp_experience_years"
            ]


        # ----------------------------------------------------
        # AWS
        # ----------------------------------------------------

        if (
            "aws" in normalized
            and (
                "experience" in normalized
                or "years" in normalized
            )
        ):

            return PROFILE_FACTS[
                "aws_experience_years"
            ]


        # ----------------------------------------------------
        # Azure
        # ----------------------------------------------------

        if (
            "azure" in normalized
            and (
                "experience" in normalized
                or "years" in normalized
            )
        ):

            return PROFILE_FACTS[
                "azure_experience_years"
            ]


        # ----------------------------------------------------
        # Python
        # ----------------------------------------------------

        if (
            "python" in normalized
            and (
                "experience" in normalized
                or "years" in normalized
            )
        ):

            return PROFILE_FACTS[
                "python_experience_years"
            ]


        # ----------------------------------------------------
        # Docker
        # ----------------------------------------------------

        if (
            "docker" in normalized
            and (
                "experience" in normalized
                or "years" in normalized
            )
        ):

            return PROFILE_FACTS[
                "docker_experience_years"
            ]


        # ----------------------------------------------------
        # Kubernetes
        # ----------------------------------------------------

        if (
            "kubernetes" in normalized
            and (
                "experience" in normalized
                or "years" in normalized
            )
        ):

            return PROFILE_FACTS[
                "kubernetes_experience_years"
            ]


        # ----------------------------------------------------
        # DevOps
        # ----------------------------------------------------

        if (
            "devops" in normalized
            and (
                "experience" in normalized
                or "years" in normalized
            )
        ):

            return PROFILE_FACTS[
                "devops_experience_years"
            ]


        # ----------------------------------------------------
        # Unknown question
        # ----------------------------------------------------

        return None


# ============================================================
# NAUKRI AUTOMATION
# ============================================================

class NaukriJobAutomation:

    def __init__(self, driver, answer_engine):

        self.driver = driver

        self.wait = WebDriverWait(
            driver,
            15
        )

        self.answer_engine = answer_engine


    # ========================================================
    # APPLICATION CONFIRMATION
    # ========================================================

    def check_application_confirmation(self):

        try:

            body_text = self.driver.find_element(
                By.TAG_NAME,
                "body"
            ).text.lower()

            confirmation_phrases = [
                "applied to",
                "application submitted",
                "successfully applied",
                "you have applied",
                "application has been submitted",
            ]

            for phrase in confirmation_phrases:

                if phrase in body_text:

                    return True, phrase

        except Exception:
            pass

        return False, None


    # ========================================================
    # EXTERNAL APPLICATION DETECTION
    # ========================================================

    def is_external_application(self):

        try:

            body_text = self.driver.find_element(
                By.TAG_NAME,
                "body"
            ).text.lower()

            external_phrases = [
                "apply on company site",
                "apply on employer site",
                "apply on company website",
                "company website",
                "external application",
            ]

            for phrase in external_phrases:

                if phrase in body_text:

                    return True

        except Exception:
            pass

        return False


    # ========================================================
    # FIND APPLY BUTTON
    # ========================================================

    def find_apply_button(self):

        # ----------------------------------------------------
        # METHOD 1
        # Naukri current Apply button class
        # ----------------------------------------------------

        selectors = [

            "button.apply-button",

            "button[class*='apply-button']",

            ".apply-button",

            "button[type='button'][class*='apply']",

        ]

        for selector in selectors:

            try:

                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    selector
                )

                for element in elements:

                    try:

                        if (
                            element.is_displayed()
                            and element.is_enabled()
                        ):

                            return element

                    except (
                        StaleElementReferenceException
                    ):

                        continue

            except Exception:
                continue


        # ----------------------------------------------------
        # METHOD 2
        # Text-based fallback
        # ----------------------------------------------------

        try:

            elements = self.driver.find_elements(
                By.XPATH,
                "//button | //a"
            )

            for element in elements:

                try:

                    if not element.is_displayed():
                        continue

                    text = clean_text(
                        element.text
                    ).lower()

                    if text == "apply":

                        return element

                except (
                    StaleElementReferenceException
                ):

                    continue

        except Exception:
            pass


        # ----------------------------------------------------
        # Method 3
        # aria-label / title fallback
        # ----------------------------------------------------

        try:

            elements = self.driver.find_elements(
                By.XPATH,
                "//*[@aria-label or @title]"
            )

            for element in elements:

                try:

                    if not element.is_displayed():
                        continue

                    aria = clean_text(
                        element.get_attribute(
                            "aria-label"
                        )
                    ).lower()

                    title = clean_text(
                        element.get_attribute(
                            "title"
                        )
                    ).lower()

                    if (
                        aria == "apply"
                        or title == "apply"
                    ):

                        return element

                except (
                    StaleElementReferenceException
                ):

                    continue

        except Exception:
            pass


        return None


    # ========================================================
    # CLICK APPLY
    # ========================================================

    def click_apply(self, button):

        try:

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                button
            )

            time.sleep(1)

            try:

                button.click()

            except (
                ElementClickInterceptedException
            ):

                self.driver.execute_script(
                    "arguments[0].click();",
                    button
                )

            time.sleep(3)

            return True

        except Exception as e:

            print(
                f"Apply button click failed: {e}"
            )

            return False


    # ========================================================
    # FIND SCREENING MODAL
    # ========================================================

    def find_screening_modal(self):

        selectors = [

            "div[role='dialog']",

            ".styles_modal__",

            "[class*='modal']",

            "[class*='Modal']",

            ".apply-question",

            "[class*='apply-question']",

        ]

        candidates = []

        for selector in selectors:

            try:

                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    selector
                )

                candidates.extend(elements)

            except Exception:
                continue


        # Remove duplicates by element id
        seen = set()

        for element in candidates:

            try:

                element_id = element.id

                if element_id in seen:
                    continue

                seen.add(element_id)

                if not element.is_displayed():
                    continue

                text = clean_text(
                    element.text
                )

                if len(text) > 10:

                    return element

            except (
                StaleElementReferenceException
            ):

                continue


        # ----------------------------------------------------
        # Generic visible overlay fallback
        # ----------------------------------------------------

        try:

            elements = self.driver.find_elements(
                By.XPATH,
                "//*[contains(@class,'modal') or "
                "contains(@class,'Modal') or "
                "@role='dialog']"
            )

            for element in elements:

                try:

                    if not element.is_displayed():
                        continue

                    text = clean_text(
                        element.text
                    )

                    if len(text) > 10:

                        return element

                except (
                    StaleElementReferenceException
                ):

                    continue

        except Exception:
            pass


        return None


    # ========================================================
    # EXTRACT QUESTION
    # ========================================================

    def extract_question(self, modal):

        try:

            text = clean_text(
                modal.text
            )

            if not text:
                return None

            lines = [
                line.strip()
                for line in text.splitlines()
                if line.strip()
            ]

            # Remove generic buttons
            ignored = {
                "save",
                "submit",
                "apply",
                "cancel",
                "close",
                "next",
                "back",
            }

            candidates = []

            for line in lines:

                if line.lower() in ignored:
                    continue

                if len(line) < 5:
                    continue

                candidates.append(line)


            # Prefer question-looking lines
            for line in candidates:

                lower = line.lower()

                if (
                    "?" in line
                    or "how many years" in lower
                    or "do you" in lower
                    or "are you" in lower
                    or "have you" in lower
                    or "experience" in lower
                    or "years" in lower
                ):

                    return line


            if candidates:

                return candidates[0]

        except Exception:
            pass

        return None


    # ========================================================
    # FIND SAVE BUTTON
    # ========================================================

    def find_save_button(self, modal):

        try:

            elements = modal.find_elements(
                By.XPATH,
                ".//button | .//input"
            )

            for element in elements:

                try:

                    if not element.is_displayed():
                        continue

                    text = clean_text(
                        element.text
                    ).lower()

                    value = clean_text(
                        element.get_attribute(
                            "value"
                        )
                    ).lower()

                    aria = clean_text(
                        element.get_attribute(
                            "aria-label"
                        )
                    ).lower()

                    if (
                        text == "save"
                        or value == "save"
                        or aria == "save"
                    ):

                        return element

                except (
                    StaleElementReferenceException
                ):

                    continue

        except Exception:
            pass

        return None


    # ========================================================
    # FIND TEXT CONTROL
    # ========================================================

    def find_text_control(self, modal):

        selectors = [

            "textarea.textArea",

            "textarea",

            "input[type='text']",

            "input:not([type='radio']):not([type='checkbox'])",

        ]

        for selector in selectors:

            try:

                elements = modal.find_elements(
                    By.CSS_SELECTOR,
                    selector
                )

                for element in elements:

                    try:

                        if element.is_displayed():

                            return element

                    except (
                        StaleElementReferenceException
                    ):

                        continue

            except Exception:
                continue

        return None


    # ========================================================
    # FIND RADIO OPTIONS
    # ========================================================

    def find_radio_options(self, modal):

        try:

            radios = modal.find_elements(
                By.CSS_SELECTOR,
                "input[type='radio']"
            )

            visible_radios = []

            for radio in radios:

                try:

                    if radio.is_displayed():

                        visible_radios.append(
                            radio
                        )

                except (
                    StaleElementReferenceException
                ):

                    continue

            return visible_radios

        except Exception:

            return []


    # ========================================================
    # SELECT RADIO ANSWER
    # ========================================================

    def select_radio_answer(
        self,
        modal,
        answer
    ):

        answer = clean_text(
            answer
        ).lower()

        radios = self.find_radio_options(
            modal
        )

        if not radios:
            return False


        # ----------------------------------------------------
        # Look for associated labels
        # ----------------------------------------------------

        for radio in radios:

            try:

                radio_id = radio.get_attribute(
                    "id"
                )

                label_text = ""

                if radio_id:

                    labels = modal.find_elements(
                        By.CSS_SELECTOR,
                        f"label[for='{radio_id}']"
                    )

                    if labels:

                        label_text = clean_text(
                            labels[0].text
                        ).lower()


                # Parent label
                if not label_text:

                    try:

                        parent = radio.find_element(
                            By.XPATH,
                            "./ancestor::label[1]"
                        )

                        label_text = clean_text(
                            parent.text
                        ).lower()

                    except Exception:
                        pass


                # Parent container
                if not label_text:

                    try:

                        parent = radio.find_element(
                            By.XPATH,
                            "./.."
                        )

                        label_text = clean_text(
                            parent.text
                        ).lower()

                    except Exception:
                        pass


                if answer in label_text:

                    self.driver.execute_script(
                        "arguments[0].click();",
                        radio
                    )

                    return True

            except Exception:
                continue


        # ----------------------------------------------------
        # Yes / No fallback
        # ----------------------------------------------------

        if answer in ["yes", "no"]:

            for radio in radios:

                try:

                    value = clean_text(
                        radio.get_attribute(
                            "value"
                        )
                    ).lower()

                    if value == answer:

                        self.driver.execute_script(
                            "arguments[0].click();",
                            radio
                        )

                        return True

                except Exception:
                    continue


        return False


    # ========================================================
    # NORMALIZE QUESTION
    # ========================================================

    def normalize_question(self, question):

        question = clean_text(
            question
        ).lower()

        question = re.sub(
            r"\s+",
            " ",
            question
        )

        return question.strip()


    # ========================================================
    # WAIT AFTER SAVE
    # ========================================================

    def wait_after_save(
        self,
        previous_question
    ):

        previous_question = self.normalize_question(
            previous_question
        )

        for _ in range(15):

            time.sleep(1)

            modal = self.find_screening_modal()

            if not modal:
                continue

            question = self.extract_question(
                modal
            )

            if not question:
                continue

            current_question = self.normalize_question(
                question
            )

            if current_question != previous_question:

                return modal

        return self.find_screening_modal()


    # ========================================================
    # PROCESS SCREENING QUESTIONS
    # ========================================================

    def process_screening_questions(self):

        print()
        print("=" * 70)
        print("PROCESSING SCREENING QUESTIONS")
        print("=" * 70)

        answered_questions = set()

        for question_number in range(
            1,
            MAX_SCREENING_QUESTIONS + 1
        ):

            print()
            print(
                f"SCREENING QUESTION {question_number}"
            )

            modal = self.find_screening_modal()

            if not modal:

                # ------------------------------------------------
                # Maybe application already completed
                # ------------------------------------------------

                confirmed, phrase = (
                    self.check_application_confirmation()
                )

                if confirmed:

                    print(
                        "Application confirmed."
                    )

                    return True, None


                # ------------------------------------------------
                # Wait a little longer for modal
                # ------------------------------------------------

                time.sleep(3)

                modal = self.find_screening_modal()

                if not modal:

                    print(
                        "No screening modal found."
                    )

                    return False, (
                        "No screening modal found."
                    )


            question = self.extract_question(
                modal
            )

            if not question:

                print(
                    "Could not extract screening question."
                )

                return False, (
                    "Could not extract screening question."
                )


            normalized_question = (
                self.normalize_question(
                    question
                )
            )


            # ------------------------------------------------
            # Duplicate protection
            # ------------------------------------------------

            if normalized_question in answered_questions:

                print(
                    "Same question detected again."
                )

                # Try waiting for a state change
                time.sleep(2)

                new_modal = (
                    self.find_screening_modal()
                )

                if new_modal:

                    new_question = (
                        self.extract_question(
                            new_modal
                        )
                    )

                    if new_question:

                        new_normalized = (
                            self.normalize_question(
                                new_question
                            )
                        )

                        if (
                            new_normalized
                            != normalized_question
                        ):

                            modal = new_modal

                            question = new_question

                            normalized_question = (
                                new_normalized
                            )

                        else:

                            return False, (
                                "Screening question "
                                "did not change after Save."
                            )


            answered_questions.add(
                normalized_question
            )


            print(
                f"Question: {question}"
            )


            # ------------------------------------------------
            # Get verified answer
            # ------------------------------------------------

            answer = self.answer_engine.get_answer(
                question
            )

            if answer is None:

                print(
                    "NO VERIFIED ANSWER AVAILABLE."
                )

                print(
                    "The automation will NOT guess."
                )

                return False, (
                    f"Unknown screening question: "
                    f"{question}"
                )


            print(
                f"Verified answer: {answer}"
            )


            # ------------------------------------------------
            # Radio question
            # ------------------------------------------------

            radios = self.find_radio_options(
                modal
            )

            if radios:

                selected = (
                    self.select_radio_answer(
                        modal,
                        answer
                    )
                )

                if not selected:

                    return False, (
                        f"Could not select answer "
                        f"'{answer}' for question: "
                        f"{question}"
                    )


            else:

                # ------------------------------------------------
                # Text question
                # ------------------------------------------------

                control = self.find_text_control(
                    modal
                )

                if not control:

                    return False, (
                        f"No answer field found for "
                        f"question: {question}"
                    )


                try:

                    control.click()

                    control.clear()

                    control.send_keys(
                        str(answer)
                    )

                except Exception as e:

                    return False, (
                        f"Could not enter answer: "
                        f"{e}"
                    )


            # ------------------------------------------------
            # Save
            # ------------------------------------------------

            save_button = self.find_save_button(
                modal
            )

            if not save_button:

                return False, (
                    "Save button not found."
                )


            try:

                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    save_button
                )

                time.sleep(0.5)

                try:

                    save_button.click()

                except (
                    ElementClickInterceptedException
                ):

                    self.driver.execute_script(
                        "arguments[0].click();",
                        save_button
                    )

            except Exception as e:

                return False, (
                    f"Could not click Save: {e}"
                )


            print(
                "Answer saved."
            )


            # ------------------------------------------------
            # Wait for next question
            # ------------------------------------------------

            self.wait_after_save(
                question
            )


            # ------------------------------------------------
            # Check application confirmation
            # ------------------------------------------------

            confirmed, phrase = (
                self.check_application_confirmation()
            )

            if confirmed:

                print()
                print(
                    "=" * 70
                )
                print(
                    "APPLICATION CONFIRMED"
                )
                print(
                    "=" * 70
                )

                print(
                    f"Detected phrase: {phrase}"
                )

                return True, None


        return False, (
            "Maximum screening question "
            "limit reached."
        )


# ============================================================
# UPDATE TRACKER
# ============================================================

def update_tracker(
    tracker_df,
    job_id,
    status,
    notes="",
    applied_date=None
):

    job_id = normalize_job_id(
        job_id
    )

    mask = (
        tracker_df["job_id"]
        .apply(normalize_job_id)
        == job_id
    )

    if not mask.any():

        print(
            f"Tracker row not found for Job ID {job_id}"
        )

        return tracker_df


    current_status = clean_text(
        tracker_df.loc[
            mask,
            "application_status"
        ].iloc[0]
    )


    # --------------------------------------------------------
    # NEVER DOWNGRADE APPLIED
    # --------------------------------------------------------

    if current_status.lower() == "applied":

        print(
            f"Job {job_id} is already Applied."
        )

        print(
            "Existing Applied status will NOT be downgraded."
        )

        return tracker_df


    tracker_df.loc[
        mask,
        "application_status"
    ] = status


    if applied_date is not None:

        tracker_df.loc[
            mask,
            "applied_date"
        ] = applied_date

    else:

        if status == "Applied":

            tracker_df.loc[
                mask,
                "applied_date"
            ] = time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )


    tracker_df.loc[
        mask,
        "application_notes"
    ] = notes


    tracker_df.to_csv(
        TRACKER_FILE,
        index=False
    )


    print(
        "Tracker updated successfully."
    )

    print(
        f"Job ID : {job_id}"
    )

    print(
        f"Status : {status}"
    )

    print(
        f"Notes  : {notes}"
    )


    return tracker_df


# ============================================================
# LOAD ALL JOBS
# ============================================================

def load_all_jobs():

    if not os.path.exists(
        TRACKER_FILE
    ):

        raise FileNotFoundError(
            TRACKER_FILE
        )


    if not os.path.exists(
        SELECTED_JOBS_FILE
    ):

        raise FileNotFoundError(
            SELECTED_JOBS_FILE
        )


    tracker = pd.read_csv(
        TRACKER_FILE
    )

    selected = pd.read_csv(
        SELECTED_JOBS_FILE
    )


    tracker = normalize_dataframe_columns(
        tracker
    )

    selected = normalize_dataframe_columns(
        selected
    )


    tracker["job_id"] = (
        tracker["job_id"]
        .apply(normalize_job_id)
    )


    url_column_tracker = find_column(
        tracker,
        ["url", "job_url"]
    )

    url_column_selected = find_column(
        selected,
        ["url", "job_url"]
    )


    if not url_column_tracker:

        raise ValueError(
            "URL column not found in application_tracker.csv"
        )


    if not url_column_selected:

        raise ValueError(
            "URL column not found in selected_jobs.csv"
        )


    selected["_url_key"] = (
        selected[url_column_selected]
        .astype(str)
        .str.strip()
    )


    jobs = []

    for _, tracker_row in tracker.iterrows():

        job_id = normalize_job_id(
            tracker_row["job_id"]
        )

        if not job_id:
            continue


        try:

            numeric_id = int(job_id)

        except ValueError:

            continue


        if numeric_id < START_JOB_ID:
            continue

        if numeric_id > END_JOB_ID:
            continue


        tracker_url = clean_text(
            tracker_row[url_column_tracker]
        )


        selected_matches = selected[
            selected["_url_key"]
            == tracker_url
        ]


        if selected_matches.empty:

            print(
                f"Warning: Selected job not found for {job_id}"
            )

            continue


        selected_row = (
            selected_matches.iloc[0]
        )


        jobs.append(
            {
                "job_id": job_id,
                "job_title": clean_text(
                    selected_row.get(
                        "job_title",
                        tracker_row.get(
                            "job_title",
                            ""
                        )
                    )
                ),
                "company": clean_text(
                    selected_row.get(
                        "company",
                        tracker_row.get(
                            "company",
                            ""
                        )
                    )
                ),
                "url": tracker_url,
                "status": clean_text(
                    tracker_row.get(
                        "application_status",
                        ""
                    )
                ),
            }
        )


    jobs.sort(
        key=lambda x: int(
            x["job_id"]
        )
    )


    return tracker, jobs


# ============================================================
# CREATE BROWSER
# ============================================================

def create_browser():

    options = webdriver.ChromeOptions()

    options.add_argument(
        "--start-maximized"
    )

    options.add_argument(
        "--disable-notifications"
    )

    driver = webdriver.Chrome(
        options=options
    )

    return driver


# ============================================================
# LOGIN
# ============================================================

def login_current_page(driver):

    print()
    print("=" * 70)
    print("CHECKING LOGIN")
    print("=" * 70)


    try:

        body_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text.lower()

        # Existing logged-in state
        if (
            "login" not in body_text
            or "logout" in body_text
            or "my naukri" in body_text
        ):

            print(
                "Existing Naukri login session detected."
            )

            return True

    except Exception:
        pass


    # --------------------------------------------------------
    # Find Login link
    # --------------------------------------------------------

    login_selectors = [

        "a.nI-gNb-lg-rg__login",

        "a[href*='login.naukri.com']",

    ]


    login_element = None


    for selector in login_selectors:

        try:

            elements = driver.find_elements(
                By.CSS_SELECTOR,
                selector
            )

            for element in elements:

                if element.is_displayed():

                    login_element = element

                    break

            if login_element:
                break

        except Exception:
            continue


    if not login_element:

        print(
            "Login link not found."
        )

        return False


    try:

        driver.execute_script(
            "arguments[0].click();",
            login_element
        )

    except Exception:

        try:

            login_element.click()

        except Exception as e:

            print(
                f"Could not click login: {e}"
            )

            return False


    time.sleep(2)


    # --------------------------------------------------------
    # Login fields
    # --------------------------------------------------------

    try:

        email_field = WebDriverWait(
            driver,
            15
        ).until(
            EC.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "input[placeholder='Enter your active Email ID / Username']"
                )
            )
        )


        password_field = WebDriverWait(
            driver,
            15
        ).until(
            EC.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "input[placeholder='Enter your password']"
                )
            )
        )


        email_field.clear()

        email_field.send_keys(
            NAUKRI_EMAIL
        )


        password_field.clear()

        password_field.send_keys(
            NAUKRI_PASSWORD
        )


        login_button = WebDriverWait(
            driver,
            15
        ).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "button.loginButton"
                )
            )
        )


        try:

            login_button.click()

        except Exception:

            driver.execute_script(
                "arguments[0].click();",
                login_button
            )


        time.sleep(5)


        print(
            "Login completed."
        )

        return True


    except Exception as e:

        print(
            f"Login failed: {e}"
        )

        return False


# ============================================================
# PROCESS SINGLE JOB
# ============================================================

def process_job(
    driver,
    automation,
    tracker_df,
    job
):

    job_id = job["job_id"]

    title = job["job_title"]

    company = job["company"]

    url = job["url"]

    current_status = clean_text(
        job["status"]
    )


    print()
    print(
        "#" * 75
    )

    print(
        f"PROCESSING JOB: {job_id}"
    )

    print(
        f"TITLE: {title}"
    )

    print(
        f"COMPANY: {company}"
    )

    print(
        f"CURRENT STATUS: {current_status}"
    )

    print(
        "#" * 75
    )


    # --------------------------------------------------------
    # Skip already completed
    # --------------------------------------------------------

    if current_status.lower() == "applied":

        print(
            f"SKIPPING: {job_id} is already Applied."
        )

        return tracker_df


    if current_status.lower() == "external site":

        print(
            f"SKIPPING: {job_id} is already marked External Site."
        )

        return tracker_df


    # --------------------------------------------------------
    # Open job
    # --------------------------------------------------------

    print()
    print(
        "=" * 70
    )

    print(
        "OPENING JOB"
    )

    print(
        "=" * 70
    )

    print(
        f"URL: {url}"
    )


    driver.get(url)

    time.sleep(4)


    print(
        f"Current URL: {driver.current_url}"
    )


    # --------------------------------------------------------
    # Login
    # --------------------------------------------------------

    if not login_current_page(
        driver
    ):

        tracker_df = update_tracker(
            tracker_df,
            job_id,
            "Review Required",
            "Login could not be completed."
        )

        return tracker_df


    # --------------------------------------------------------
    # Re-open job after login if necessary
    # --------------------------------------------------------

    if url not in driver.current_url:

        driver.get(url)

        time.sleep(4)


    # --------------------------------------------------------
    # Check already applied
    # --------------------------------------------------------

    confirmed, phrase = (
        automation.check_application_confirmation()
    )


    if confirmed:

        print()
        print(
            "APPLICATION ALREADY CONFIRMED"
        )

        tracker_df = update_tracker(
            tracker_df,
            job_id,
            "Applied",
            "Application confirmed by Naukri."
        )

        return tracker_df


    # --------------------------------------------------------
    # Check external application
    # --------------------------------------------------------

    print()
    print(
        "=" * 70
    )

    print(
        "CHECKING APPLICATION TYPE"
    )

    print(
        "=" * 70
    )


    if automation.is_external_application():

        print(
            "EXTERNAL APPLICATION DETECTED."
        )

        print(
            "The automation will NOT click the company site."
        )


        tracker_df = update_tracker(
            tracker_df,
            job_id,
            "External Site",
            "Naukri requires application on company site."
        )

        return tracker_df


    # --------------------------------------------------------
    # Find Apply button
    # --------------------------------------------------------

    print()
    print(
        "=" * 70
    )

    print(
        "FINDING NAUKRI APPLY BUTTON"
    )

    print(
        "=" * 70
    )


    apply_button = automation.find_apply_button()


    if not apply_button:

        print(
            "Normal Naukri Apply button was not found."
        )

        print(
            "No external-site click will be performed."
        )


        tracker_df = update_tracker(
            tracker_df,
            job_id,
            "Review Required",
            "Normal Naukri Apply button was not found."
        )

        return tracker_df


    print(
        "Normal Naukri Apply button found."
    )


    # --------------------------------------------------------
    # Click Apply
    # --------------------------------------------------------

    if not automation.click_apply(
        apply_button
    ):

        tracker_df = update_tracker(
            tracker_df,
            job_id,
            "Review Required",
            "Naukri Apply button was found but could not be clicked."
        )

        return tracker_df


    print(
        "Apply button clicked."
    )


    # --------------------------------------------------------
    # Check immediate confirmation
    # --------------------------------------------------------

    time.sleep(2)


    confirmed, phrase = (
        automation.check_application_confirmation()
    )


    if confirmed:

        print()
        print(
            "=" * 70
        )

        print(
            "APPLICATION CONFIRMED"
        )

        print(
            "=" * 70
        )

        print(
            f"Detected phrase: {phrase}"
        )


        tracker_df = update_tracker(
            tracker_df,
            job_id,
            "Applied",
            "Application confirmed by Naukri."
        )

        return tracker_df


    # --------------------------------------------------------
    # Process screening
    # --------------------------------------------------------

    success, reason = (
        automation.process_screening_questions()
    )


    if success:

        print()
        print(
            "=" * 70
        )

        print(
            "APPLICATION CONFIRMED"
        )

        print(
            "=" * 70
        )


        tracker_df = update_tracker(
            tracker_df,
            job_id,
            "Applied",
            "Application confirmed by Naukri."
        )

        return tracker_df


    # --------------------------------------------------------
    # Review required
    # --------------------------------------------------------

    print()
    print(
        "APPLICATION NOT CONFIRMED."
    )

    print(
        f"Reason: {reason}"
    )


    tracker_df = update_tracker(
        tracker_df,
        job_id,
        "Review Required",
        reason
    )


    return tracker_df


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=" * 75
    )

    print(
        "        NAUKRI BATCH APPLICATION AUTOMATION"
    )

    print(
        "=" * 75
    )


    if not NAUKRI_EMAIL or not NAUKRI_PASSWORD:

        print(
            "ERROR: NAUKRI_EMAIL or NAUKRI_PASSWORD missing in .env"
        )

        return


    # --------------------------------------------------------
    # Load jobs
    # --------------------------------------------------------

    try:

        tracker_df, jobs = load_all_jobs()

    except Exception as e:

        print(
            f"Could not load jobs: {e}"
        )

        return


    print()
    print(
        f"Jobs loaded: {len(jobs)}"
    )

    print(
        f"Processing range: "
        f"{START_JOB_ID:03d} to {END_JOB_ID:03d}"
    )


    # --------------------------------------------------------
    # Answer database
    # --------------------------------------------------------

    answer_database = AnswerDatabase(
        ANSWERS_FILE
    )

    answer_engine = ProfileAnswerEngine(
        answer_database
    )


    # --------------------------------------------------------
    # Browser
    # --------------------------------------------------------

    driver = create_browser()

    automation = NaukriJobAutomation(
        driver,
        answer_engine
    )


    try:

        # ----------------------------------------------------
        # Open first job
        # ----------------------------------------------------

        if jobs:

            driver.get(
                jobs[0]["url"]
            )

            time.sleep(4)


            if not login_current_page(
                driver
            ):

                print()
                print(
                    "LOGIN FAILED."
                )

                print(
                    "Stopping batch to avoid incorrect processing."
                )

                return


        # ----------------------------------------------------
        # Process all jobs
        # ----------------------------------------------------

        for index, job in enumerate(
            jobs,
            start=1
        ):

            try:

                tracker_df = process_job(
                    driver,
                    automation,
                    tracker_df,
                    job
                )

            except Exception as e:

                print()
                print(
                    "=" * 70
                )

                print(
                    f"ERROR PROCESSING JOB {job['job_id']}"
                )

                print(
                    f"Error: {e}"
                )

                print(
                    "=" * 70
                )


                tracker_df = update_tracker(
                    tracker_df,
                    job["job_id"],
                    "Review Required",
                    f"Automation error: {e}"
                )


            print()
            print(
                f"Moving to next job in "
                f"{WAIT_BETWEEN_JOBS} seconds..."
            )

            time.sleep(
                WAIT_BETWEEN_JOBS
            )


        # ----------------------------------------------------
        # Complete
        # ----------------------------------------------------

        print()
        print(
            "=" * 75
        )

        print(
            "ALL SELECTED JOBS PROCESSED"
        )

        print(
            "=" * 75
        )

        print(
            f"Processed range: "
            f"{START_JOB_ID:03d} to {END_JOB_ID:03d}"
        )

        print()
        print(
            "Check application_tracker.csv "
            "for final statuses."
        )

        print(
            "=" * 75
        )


        print()
        print(
            "Browser will remain open for 30 seconds."
        )

        time.sleep(30)


    finally:

        driver.quit()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()