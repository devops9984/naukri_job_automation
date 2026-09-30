import re
from datetime import date
from dateutil.relativedelta import relativedelta


# ============================================================
# RESUME EMPLOYMENT DATA
# ============================================================
#
# IMPORTANT:
# A skill gets experience only when it is documented as being
# used in that employment/project period.
#
# A skill appearing only in "Technical Skills" does NOT
# automatically receive the entire career duration.
# ============================================================

EMPLOYMENT_HISTORY = [
    {
        "company": "GlobalLogic Technologies Pvt Ltd",
        "start": "2022-03",
        "end": "2024-07",
        "skills": [
            "aws",
            "ec2",
            "iam",
            "vpc",
            "s3",
            "ebs",
            "load balancer",
            "terraform",
            "docker",
            "kubernetes",
            "jenkins",
            "git",
            "prometheus",
            "grafana",
            "cloudwatch",
            "bash",
            "python",
            "linux",
            "ci/cd",
        ],
    },

    {
        "company": "Bees Soft",
        "start": "2021-03",
        "end": "2022-01",
        "skills": [
            "aws",
            "ec2",
            "s3",
            "iam",
            "docker",
            "kubernetes",
            "jenkins",
            "github actions",
            "terraform",
            "git",
            "cloudwatch",
            "bash",
            "python",
            "linux",
            "ci/cd",
        ],
    },
]


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_skill(skill):

    skill = skill.lower().strip()

    skill = skill.replace("amazon web services", "aws")
    skill = skill.replace("amazon cloudwatch", "cloudwatch")
    skill = skill.replace("k8s", "kubernetes")
    skill = skill.replace("iac", "terraform")
    skill = skill.replace("continuous integration/continuous deployment", "ci/cd")

    skill = re.sub(r"\s+", " ", skill)

    return skill


# ============================================================
# DATE PARSER
# ============================================================

def parse_month(value):

    year, month = value.split("-")

    return date(
        int(year),
        int(month),
        1
    )


# ============================================================
# CALCULATE MONTHS
# ============================================================

def calculate_months(start, end):

    start_date = parse_month(start)
    end_date = parse_month(end)

    difference = relativedelta(
        end_date,
        start_date
    )

    months = (
        difference.years * 12
        + difference.months
    )

    # Include the employment end month
    months += 1

    return months


# ============================================================
# FORMAT EXPERIENCE
# ============================================================

def format_experience(months):

    years = months // 12
    remaining_months = months % 12

    if years == 0:
        return f"{remaining_months} months"

    if remaining_months == 0:

        if years == 1:
            return "1 year"

        return f"{years} years"

    if years == 1:

        return f"1 year {remaining_months} months"

    return f"{years} years {remaining_months} months"


# ============================================================
# CALCULATE SKILL EXPERIENCE
# ============================================================

def calculate_skill_experience(skill):

    requested_skill = normalize_skill(skill)

    total_months = 0

    matching_companies = []

    for job in EMPLOYMENT_HISTORY:

        normalized_skills = [
            normalize_skill(item)
            for item in job["skills"]
        ]

        if requested_skill in normalized_skills:

            months = calculate_months(
                job["start"],
                job["end"]
            )

            total_months += months

            matching_companies.append({
                "company": job["company"],
                "start": job["start"],
                "end": job["end"],
                "months": months
            })

    return {
        "skill": skill,
        "months": total_months,
        "years_decimal": round(
            total_months / 12,
            1
        ),
        "formatted": format_experience(
            total_months
        ),
        "companies": matching_companies,
        "status": (
            "CALCULATED"
            if total_months > 0
            else "NO_DOCUMENTED_EXPERIENCE"
        )
    }


# ============================================================
# GET YEARS FOR APPLICATION FORMS
# ============================================================

def get_skill_years(skill):

    result = calculate_skill_experience(
        skill
    )

    if result["status"] != "CALCULATED":

        return None

    return result["years_decimal"]


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_skills = [
        "AWS",
        "Docker",
        "Kubernetes",
        "Terraform",
        "Jenkins",
        "Python",
        "Prometheus",
        "Grafana",
        "Linux",
        "Git",
        "GCP"
    ]

    print("=" * 70)
    print("SKILL EXPERIENCE CALCULATOR")
    print("=" * 70)

    for skill in test_skills:

        result = calculate_skill_experience(
            skill
        )

        print("\nSkill:")
        print(skill)

        print(
            "Experience:",
            result["formatted"]
        )

        print(
            "Decimal:",
            result["years_decimal"]
        )

        print(
            "Status:",
            result["status"]
        )

        if result["companies"]:

            print("Documented through:")

            for company in result["companies"]:

                print(
                    f"  {company['company']} "
                    f"({company['start']} → {company['end']})"
                )

        print("-" * 70)