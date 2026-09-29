import csv
import os
import re
import logging

from docx import Document


# ============================================================
# CONFIGURATION
# ============================================================

MASTER_RESUME = os.path.join(
    "master_resume",
    "master_resume.docx"
)

JOB_DETAILS_FILE = "job_details.csv"

OUTPUT_DIR = "generated_resumes"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# ============================================================
# SKILLS / KEYWORDS
# ============================================================

SKILLS = [
    "aws",
    "azure",
    "gcp",
    "linux",
    "git",
    "github",
    "jenkins",
    "gitlab",
    "ci/cd",
    "cicd",
    "docker",
    "kubernetes",
    "eks",
    "terraform",
    "ansible",
    "helm",
    "prometheus",
    "grafana",
    "cloudwatch",
    "cloudtrail",
    "iam",
    "ec2",
    "s3",
    "rds",
    "lambda",
    "dynamodb",
    "vpc",
    "elb",
    "load balancer",
    "nginx",
    "apache",
    "tomcat",
    "sonarqube",
    "nexus",
    "artifactory",
    "python",
    "bash",
    "monitoring",
    "troubleshooting",
    "incident management",
    "production support",
    "l2",
    "l3",
    "sre",
    "devops",
    "cloud",
    "infrastructure",
    "deployment",
    "backup",
    "disaster recovery",
    "blue green",
    "canary",
]


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize(text):

    if not text:
        return ""

    text = text.lower()

    text = text.replace(
        "continuous integration",
        "ci/cd"
    )

    text = text.replace(
        "continuous delivery",
        "ci/cd"
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# READ JOB DETAILS
# ============================================================

def read_jobs():

    logger.info(
        f"Reading {JOB_DETAILS_FILE}"
    )

    jobs = []

    with open(
        JOB_DETAILS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            if row.get(
                "full_job_description",
                ""
            ).strip():

                jobs.append(row)

    logger.info(
        f"Jobs with full JD: {len(jobs)}"
    )

    return jobs


# ============================================================
# READ MASTER RESUME
# ============================================================

def read_master_resume():

    logger.info(
        f"Reading {MASTER_RESUME}"
    )

    document = Document(
        MASTER_RESUME
    )

    paragraphs = []

    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if not text:
            continue

        paragraphs.append(
            {
                "text": text,
                "style": paragraph.style.name
            }
        )

    logger.info(
        f"Resume paragraphs found: "
        f"{len(paragraphs)}"
    )

    return paragraphs


# ============================================================
# FIND JD SKILLS
# ============================================================

def find_jd_skills(jd):

    jd_text = normalize(jd)

    found = []

    for skill in SKILLS:

        if skill in jd_text:

            found.append(skill)

    return found


# ============================================================
# SCORE RESUME PARAGRAPH
# ============================================================

def score_paragraph(
    paragraph_text,
    jd_skills
):

    text = normalize(
        paragraph_text
    )

    score = 0
    matched = []

    for skill in jd_skills:

        if skill in text:

            score += 1

            matched.append(
                skill
            )

    return score, matched


# ============================================================
# ANALYZE RESUME
# ============================================================

def analyze_resume(
    resume_paragraphs,
    jd_skills
):

    scored = []

    for item in resume_paragraphs:

        score, matched = score_paragraph(
            item["text"],
            jd_skills
        )

        scored.append(
            {
                "text": item["text"],
                "style": item["style"],
                "score": score,
                "matched": matched
            }
        )

    return scored


# ============================================================
# CREATE SAFE FILENAME
# ============================================================

def safe_filename(text):

    text = re.sub(
        r'[<>:"/\\|?*]',
        "",
        text
    )

    text = re.sub(
        r"\s+",
        "_",
        text.strip()
    )

    return text[:100]


# ============================================================
# CREATE TAILORED RESUME
# ============================================================

def create_tailored_resume(
    job,
    resume_paragraphs,
    output_number
):

    title = job.get(
        "job_title",
        "Job"
    )

    company = job.get(
        "company",
        "Company"
    )

    jd = job.get(
        "full_job_description",
        ""
    )

    # --------------------------------------------------------
    # Find JD skills
    # --------------------------------------------------------

    jd_skills = find_jd_skills(
        jd
    )

    logger.info(
        f"JD skills: {', '.join(jd_skills)}"
    )

    # --------------------------------------------------------
    # Score resume content
    # --------------------------------------------------------

    scored = analyze_resume(
        resume_paragraphs,
        jd_skills
    )

    # --------------------------------------------------------
    # Sort relevant content first
    # --------------------------------------------------------

    scored.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # --------------------------------------------------------
    # Create new document
    # --------------------------------------------------------

    document = Document()

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    heading = document.add_heading(
        level=1
    )

    heading.add_run(
        "Targeted Resume"
    )

    document.add_paragraph(
        f"{title} — {company}"
    )

    document.add_paragraph(
        "This resume was generated by "
        "prioritizing existing resume content "
        "that matches the job description."
    )

    # --------------------------------------------------------
    # Targeted Skills
    # --------------------------------------------------------

    document.add_heading(
        "JD-Matched Skills",
        level=2
    )

    if jd_skills:

        matched_skills = []

        for skill in jd_skills:

            # Check whether skill actually exists
            # in the master resume.

            exists = False

            for item in resume_paragraphs:

                if skill in normalize(
                    item["text"]
                ):

                    exists = True

                    break

            if exists:

                matched_skills.append(
                    skill
                )

        if matched_skills:

            document.add_paragraph(
                ", ".join(
                    matched_skills
                )
            )

        else:

            document.add_paragraph(
                "No JD skills were found "
                "directly in the master resume."
            )

    # --------------------------------------------------------
    # Relevant Resume Content
    # --------------------------------------------------------

    document.add_heading(
        "Relevant Experience",
        level=2
    )

    relevant = [
        item
        for item in scored
        if item["score"] > 0
    ]

    if relevant:

        for item in relevant:

            paragraph = document.add_paragraph()

            paragraph.add_run(
                item["text"]
            )

    else:

        document.add_paragraph(
            "No directly matching resume "
            "content was identified."
        )

    # --------------------------------------------------------
    # Full Master Resume Content
    # --------------------------------------------------------

    document.add_heading(
        "Master Resume Content",
        level=2
    )

    for item in resume_paragraphs:

        paragraph = document.add_paragraph()

        paragraph.add_run(
            item["text"]
        )

    # --------------------------------------------------------
    # JD Reference
    # --------------------------------------------------------

    document.add_heading(
        "Job Description Reference",
        level=2
    )

    document.add_paragraph(
        jd
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    filename = (
        f"{output_number:02d}_"
        f"{safe_filename(company)}_"
        f"{safe_filename(title)}.docx"
    )

    output_path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    document.save(
        output_path
    )

    logger.info(
        f"Created: {output_path}"
    )

    return output_path


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("           JD → RESUME TAILOR")
    print("=" * 70)

    # --------------------------------------------------------
    # Check master resume
    # --------------------------------------------------------

    if not os.path.exists(
        MASTER_RESUME
    ):

        logger.error(
            f"Master resume not found:"
            f" {MASTER_RESUME}"
        )

        return

    # --------------------------------------------------------
    # Read data
    # --------------------------------------------------------

    jobs = read_jobs()

    if not jobs:

        logger.error(
            "No jobs with full JD found."
        )

        return

    resume = read_master_resume()

    if not resume:

        logger.error(
            "Master resume is empty."
        )

        return

    # --------------------------------------------------------
    # Generate resumes
    # --------------------------------------------------------

    generated = 0

    # For first test, process only first 5 jobs.
    # We can remove this limit later.

    test_jobs = jobs[:5]

    for index, job in enumerate(
        test_jobs,
        start=1
    ):

        print()

        logger.info(
            f"Processing {index}/{len(test_jobs)}"
        )

        logger.info(
            f"Job: {job.get('job_title')}"
        )

        logger.info(
            f"Company: {job.get('company')}"
        )

        try:

            create_tailored_resume(
                job,
                resume,
                index
            )

            generated += 1

        except Exception as e:

            logger.error(
                f"Failed: {e}"
            )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("              COMPLETE")
    print("=" * 70)

    print(
        f"Resumes generated: {generated}"
    )

    print(
        f"Folder: {OUTPUT_DIR}"
    )

    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()