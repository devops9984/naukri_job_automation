import csv
import re

import profile_config
from skill_experience import get_skill_years


ANSWERS_FILE = "application_answers.csv"


class AnswerEngine:

    def __init__(self):
        self.verified_answers = self.load_verified_answers()

    # =========================================================
    # LOAD VERIFIED ANSWERS
    # =========================================================

    def load_verified_answers(self):

        answers = []

        try:
            with open(
                ANSWERS_FILE,
                "r",
                encoding="utf-8-sig"
            ) as file:

                reader = csv.DictReader(file)

                for row in reader:

                    status = row.get(
                        "status",
                        ""
                    ).strip().upper()

                    # Support older CSV files that don't have
                    # a status column.
                    if status and status != "VERIFIED":
                        continue

                    question = row.get(
                        "question_pattern",
                        ""
                    ).strip()

                    answer = row.get(
                        "answer",
                        ""
                    ).strip()

                    if question and answer:

                        answers.append({
                            "question": question,
                            "answer": answer
                        })

        except FileNotFoundError:

            print(
                f"WARNING: {ANSWERS_FILE} not found"
            )

        return answers

    # =========================================================
    # NORMALIZE TEXT
    # =========================================================

    @staticmethod
    def normalize(text):

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # =========================================================
    # FIND VERIFIED ANSWER
    # =========================================================

    def find_verified_answer(self, question):

        normalized_question = self.normalize(
            question
        )

        for item in self.verified_answers:

            stored_question = self.normalize(
                item["question"]
            )

            if normalized_question == stored_question:

                return {
                    "answer": item["answer"],
                    "source": "VERIFIED_DATABASE",
                    "status": "VERIFIED"
                }

        return None

    # =========================================================
    # DETECT TECHNICAL SKILL
    # =========================================================

    def detect_skill(self, question):

        q = self.normalize(question)

        skills = [
            "aws",
            "gcp",
            "azure",
            "docker",
            "kubernetes",
            "terraform",
            "jenkins",
            "python",
            "prometheus",
            "grafana",
            "linux",
            "git",
            "ci cd"
        ]

        for skill in skills:

            normalized_skill = self.normalize(
                skill
            )

            if normalized_skill in q:

                return skill

        return None

    # =========================================================
    # CLASSIFY QUESTION
    # =========================================================

    def classify_question(self, question):

        q = self.normalize(question)

        # -----------------------------------------------------
        # COUNTRY OF CITIZENSHIP
        # IMPORTANT:
        # Check before generic citizenship.
        # -----------------------------------------------------

        if "country of citizenship" in q:

            return "COUNTRY_OF_CITIZENSHIP"

        # -----------------------------------------------------
        # NOTICE PERIOD
        # -----------------------------------------------------

        if any(
            word in q
            for word in [
                "notice period",
                "notice",
                "joining time",
                "when can you join",
                "how soon can you join",
                "availability to join"
            ]
        ):

            return "NOTICE_PERIOD"

        # -----------------------------------------------------
        # CITIZENSHIP / NATIONALITY
        # -----------------------------------------------------

        if any(
            word in q
            for word in [
                "citizenship",
                "citizen",
                "nationality"
            ]
        ):

            return "CITIZENSHIP"

        # -----------------------------------------------------
        # WORK AUTHORIZATION
        # -----------------------------------------------------

        if any(
            word in q
            for word in [
                "work authorization",
                "authorized to work",
                "legally authorized",
                "right to work"
            ]
        ):

            return "WORK_AUTHORIZATION"

        # -----------------------------------------------------
        # SPONSORSHIP
        # -----------------------------------------------------

        if any(
            word in q
            for word in [
                "sponsorship",
                "visa sponsorship",
                "require sponsorship",
                "need sponsorship"
            ]
        ):

            return "SPONSORSHIP"

        # -----------------------------------------------------
        # SALARY
        # -----------------------------------------------------

        if any(
            word in q
            for word in [
                "expected salary",
                "salary expectation",
                "desired salary",
                "annual compensation",
                "expected compensation"
            ]
        ):

            return "SALARY"

        # -----------------------------------------------------
        # RELOCATION
        # -----------------------------------------------------

        if any(
            word in q
            for word in [
                "relocate",
                "relocation",
                "willing to move"
            ]
        ):

            return "RELOCATION"

        # -----------------------------------------------------
        # SKILL EXPERIENCE
        #
        # First detect the technical skill.
        # Then look for experience-related language.
        # -----------------------------------------------------

        skill = self.detect_skill(question)

        if skill:

            experience_indicators = [
                "experience",
                "years",
                "year",
                "worked",
                "working",
                "hands on",
                "hands-on"
            ]

            if any(
                indicator in q
                for indicator in experience_indicators
            ):

                return "SKILL_EXPERIENCE"

        # -----------------------------------------------------
        # UNKNOWN
        # -----------------------------------------------------

        return "UNKNOWN"

    # =========================================================
    # CALCULATE SKILL EXPERIENCE ANSWER
    # =========================================================

    def get_skill_experience_answer(
        self,
        question
    ):

        skill = self.detect_skill(question)

        if not skill:

            return None

        years = get_skill_years(skill)

        if years is None:

            return None

        # Convert decimal years to months.
        total_months = round(
            years * 12
        )

        whole_years = total_months // 12
        months = total_months % 12

        # Build human-readable answer.

        if whole_years == 0:

            answer = f"{months} months"

        elif months == 0:

            answer = f"{whole_years} years"

        else:

            answer = (
                f"{whole_years} years "
                f"{months} months"
            )

        return {
            "answer": answer,
            "source": "CALCULATED_SKILL_EXPERIENCE",
            "status": "CALCULATED",
            "skill": skill
        }

    # =========================================================
    # MAIN ANSWER FUNCTION
    # =========================================================

    def get_answer(self, question):

        # =====================================================
        # PRIORITY 1
        # VERIFIED ANSWER DATABASE
        # =====================================================

        verified = self.find_verified_answer(
            question
        )

        if verified:

            return verified

        # =====================================================
        # PRIORITY 2
        # CLASSIFY QUESTION
        # =====================================================

        category = self.classify_question(
            question
        )

        # =====================================================
        # NOTICE PERIOD
        # =====================================================

        if category == "NOTICE_PERIOD":

            return {
                "answer": profile_config.NOTICE_PERIOD,
                "source": "PROFILE_CONFIG",
                "status": "CONFIGURED"
            }

        # =====================================================
        # COUNTRY OF CITIZENSHIP
        # =====================================================

        if category == "COUNTRY_OF_CITIZENSHIP":

            return {
                "answer": profile_config.COUNTRY_OF_CITIZENSHIP,
                "source": "PROFILE_CONFIG",
                "status": "CONFIGURED"
            }

        # =====================================================
        # CITIZENSHIP / NATIONALITY
        # =====================================================

        if category == "CITIZENSHIP":

            return {
                "answer": profile_config.CITIZENSHIP,
                "source": "PROFILE_CONFIG",
                "status": "CONFIGURED"
            }

        # =====================================================
        # SKILL EXPERIENCE
        # =====================================================

        if category == "SKILL_EXPERIENCE":

            skill_answer = (
                self.get_skill_experience_answer(
                    question
                )
            )

            if skill_answer:

                return skill_answer

            return {
                "answer": profile_config.UNKNOWN_ANSWER,
                "source": "NO_DOCUMENTED_EXPERIENCE",
                "status": "REVIEW_REQUIRED"
            }

        # =====================================================
        # WORK AUTHORIZATION
        # =====================================================

        if category == "WORK_AUTHORIZATION":

            if (
                profile_config.WORK_AUTHORIZATION
                is not None
            ):

                return {
                    "answer": profile_config.WORK_AUTHORIZATION,
                    "source": "PROFILE_CONFIG",
                    "status": "CONFIGURED"
                }

            return {
                "answer": profile_config.UNKNOWN_ANSWER,
                "source": "NOT_CONFIGURED",
                "status": "REVIEW_REQUIRED"
            }

        # =====================================================
        # SPONSORSHIP
        # =====================================================

        if category == "SPONSORSHIP":

            if (
                profile_config.REQUIRES_SPONSORSHIP
                is not None
            ):

                return {
                    "answer": profile_config.REQUIRES_SPONSORSHIP,
                    "source": "PROFILE_CONFIG",
                    "status": "CONFIGURED"
                }

            return {
                "answer": profile_config.UNKNOWN_ANSWER,
                "source": "NOT_CONFIGURED",
                "status": "REVIEW_REQUIRED"
            }

        # =====================================================
        # SALARY
        # =====================================================

        if category == "SALARY":

            if (
                profile_config.EXPECTED_SALARY
                is not None
            ):

                return {
                    "answer": profile_config.EXPECTED_SALARY,
                    "source": "PROFILE_CONFIG",
                    "status": "CONFIGURED"
                }

            return {
                "answer": profile_config.UNKNOWN_ANSWER,
                "source": "NOT_CONFIGURED",
                "status": "REVIEW_REQUIRED"
            }

        # =====================================================
        # RELOCATION
        # =====================================================

        if category == "RELOCATION":

            if (
                profile_config.WILLING_TO_RELOCATE
                is not None
            ):

                return {
                    "answer": profile_config.WILLING_TO_RELOCATE,
                    "source": "PROFILE_CONFIG",
                    "status": "CONFIGURED"
                }

            return {
                "answer": profile_config.UNKNOWN_ANSWER,
                "source": "NOT_CONFIGURED",
                "status": "REVIEW_REQUIRED"
            }

        # =====================================================
        # UNKNOWN QUESTION
        # =====================================================

        return {
            "answer": profile_config.UNKNOWN_ANSWER,
            "source": "UNKNOWN",
            "status": "REVIEW_REQUIRED"
        }


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":

    engine = AnswerEngine()

    test_questions = [

        # -----------------------------------------------------
        # VERIFIED DATABASE
        # -----------------------------------------------------

        "How many years of experience do you have in GCP?",

        "How many years of experience do you have in LLM?",

        "Do you hold experience in healthcare domain?",

        # -----------------------------------------------------
        # CALCULATED SKILL EXPERIENCE
        # -----------------------------------------------------

        "How many years of AWS experience do you have?",

        "How many years of Docker experience do you have?",

        "How many years of Kubernetes experience do you have?",

        "How many years of Terraform experience do you have?",

        "How many years of Jenkins experience do you have?",

        "How many years of Python experience do you have?",

        "How many years of Prometheus experience do you have?",

        "How many years of Grafana experience do you have?",

        "How many years of Linux experience do you have?",

        "How many years of Git experience do you have?",

        # -----------------------------------------------------
        # PROFILE RULES
        # -----------------------------------------------------

        "What is your notice period?",

        "What is your nationality?",

        "What is your country of citizenship?",

        # -----------------------------------------------------
        # REVIEW REQUIRED
        # -----------------------------------------------------

        "Are you authorized to work in India?",

        "Will you require visa sponsorship?",

        "What is your expected salary?",

        "Are you willing to relocate?"
    ]

    print("=" * 70)
    print("ANSWER ENGINE TEST")
    print("=" * 70)

    for question in test_questions:

        result = engine.get_answer(
            question
        )

        print()
        print("Question:")
        print(question)

        print("Answer:")
        print(result["answer"])

        print("Source:")
        print(result["source"])

        print("Status:")
        print(result["status"])

        if "skill" in result:

            print("Skill:")
            print(result["skill"])

        print("-" * 70)