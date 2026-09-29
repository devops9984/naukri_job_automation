import csv
import re
import os
from docx import Document


# =========================
# CONFIG
# =========================

MASTER_RESUME = "master_resume/master_resume.docx"
JOB_DETAILS_FILE = "job_details.csv"
OUTPUT_FILE = "jd_analysis.csv"


# Skills / technologies we want to detect
SKILLS = [
    "AWS",
    "Azure",
    "GCP",
    "Linux",
    "Git",
    "GitHub",
    "Jenkins",
    "GitLab",
    "CI/CD",
    "Docker",
    "Kubernetes",
    "EKS",
    "Terraform",
    "Ansible",
    "Helm",
    "Prometheus",
    "Grafana",
    "CloudWatch",
    "CloudTrail",
    "IAM",
    "EC2",
    "S3",
    "RDS",
    "Lambda",
    "DynamoDB",
    "VPC",
    "ELB",
    "Load Balancer",
    "Nginx",
    "Apache",
    "Tomcat",
    "SonarQube",
    "Nexus",
    "Artifactory",
    "Python",
    "Bash",
    "Monitoring",
    "Troubleshooting",
    "Incident Management",
    "Production Support",
    "L2/L3",
    "SRE",
    "DevOps",
    "Cloud",
    "Infrastructure",
    "Deployment",
    "Backup",
    "Disaster Recovery",
    "Blue-Green",
    "Canary",
    "Networking",
]


# =========================
# LOAD MASTER RESUME
# =========================

def load_resume():
    if not os.path.exists(MASTER_RESUME):
        raise FileNotFoundError(
            f"Master resume not found: {MASTER_RESUME}"
        )

    doc = Document(MASTER_RESUME)

    paragraphs = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()

        if text:
            paragraphs.append(text)

    return paragraphs


# =========================
# NORMALIZE TEXT
# =========================

def normalize(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


# =========================
# FIND SKILLS
# =========================

def find_skills(text):
    text_normalized = normalize(text)

    found = []

    for skill in SKILLS:
        skill_normalized = normalize(skill)

        if skill_normalized in text_normalized:
            found.append(skill)

    return found


# =========================
# FIND EXPERIENCE REQUIREMENT
# =========================

def extract_experience(jd):
    patterns = [
        r"(\d+)\s*[-to]+\s*(\d+)\s*(?:years|yrs)",
        r"(\d+)\s*\+\s*(?:years|yrs)",
        r"(\d+)\s*(?:years|yrs)\s*(?:of)?\s*experience",
    ]

    jd_lower = jd.lower()

    for pattern in patterns:
        match = re.search(pattern, jd_lower)

        if match:
            numbers = match.groups()

            if len(numbers) == 2:
                return f"{numbers[0]}-{numbers[1]} years"

            if len(numbers) == 1:
                return f"{numbers[0]}+ years"

    return "Not specified"


# =========================
# FIND RELEVANT RESUME CONTENT
# =========================

def find_relevant_paragraphs(resume_paragraphs, jd_skills):
    results = []

    for paragraph in resume_paragraphs:

        paragraph_skills = find_skills(paragraph)

        matched = [
            skill
            for skill in paragraph_skills
            if skill in jd_skills
        ]

        if matched:
            results.append({
                "text": paragraph,
                "skills": matched,
                "score": len(matched)
            })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results


# =========================
# ANALYZE ONE JOB
# =========================

def analyze_job(job, resume_text, resume_paragraphs):

    title = job.get("job_title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    experience = job.get("experience", "")
    salary = job.get("salary", "")
    url = job.get("url", "")
    jd = job.get("full_job_description", "")

    # Skills required by JD
    jd_skills = find_skills(jd)

    # Skills actually found in master resume
    resume_skills = find_skills(resume_text)

    strong_matches = []
    missing_skills = []

    for skill in jd_skills:

        if skill in resume_skills:
            strong_matches.append(skill)
        else:
            missing_skills.append(skill)

    # Relevant paragraphs
    relevant_paragraphs = find_relevant_paragraphs(
        resume_paragraphs,
        jd_skills
    )

    # Match percentage
    if jd_skills:
        match_percentage = round(
            (len(strong_matches) / len(jd_skills)) * 100,
            2
        )
    else:
        match_percentage = 0

    # Classification
    if match_percentage >= 75:
        category = "Strong Match"
    elif match_percentage >= 50:
        category = "Partial Match"
    else:
        category = "Low Match"

    # Recommendations
    recommendations = []

    if strong_matches:
        recommendations.append(
            "Prioritize these skills: "
            + ", ".join(strong_matches)
        )

    if relevant_paragraphs:
        recommendations.append(
            "Move JD-relevant experience and projects higher in the resume"
        )

    if missing_skills:
        recommendations.append(
            "Do not add missing skills unless they are genuinely part of your experience"
        )

    recommendations.append(
        "Keep the original resume facts unchanged"
    )

    return {
        "job_title": title,
        "company": company,
        "location": location,
        "experience_required": experience,
        "salary": salary,
        "url": url,
        "jd_experience_detected": extract_experience(jd),
        "jd_skills": ", ".join(jd_skills),
        "matched_skills": ", ".join(strong_matches),
        "missing_skills": ", ".join(missing_skills),
        "match_percentage": match_percentage,
        "category": category,
        "relevant_resume_sections": " || ".join(
            item["text"]
            for item in relevant_paragraphs[:10]
        ),
        "recommendations": " | ".join(recommendations),
    }


# =========================
# MAIN
# =========================

def main():

    print("\n==============================")
    print("JD ANALYZER STARTED")
    print("==============================\n")

    # Load resume
    resume_paragraphs = load_resume()

    resume_text = " ".join(resume_paragraphs)

    print(
        f"Loaded {len(resume_paragraphs)} resume paragraphs"
    )

    # Load jobs
    if not os.path.exists(JOB_DETAILS_FILE):
        raise FileNotFoundError(
            f"Job details file not found: {JOB_DETAILS_FILE}"
        )

    with open(
        JOB_DETAILS_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        jobs = list(csv.DictReader(file))

    print(
        f"Loaded {len(jobs)} job descriptions\n"
    )

    results = []

    for index, job in enumerate(jobs, start=1):

        title = job.get("job_title", "")
        company = job.get("company", "")

        print(
            f"[{index}/{len(jobs)}] Analyzing: "
            f"{title} - {company}"
        )

        result = analyze_job(
            job,
            resume_text,
            resume_paragraphs
        )

        results.append(result)

    # Sort by match percentage
    results.sort(
        key=lambda x: float(x["match_percentage"]),
        reverse=True
    )

    # Save
    fieldnames = [
        "job_title",
        "company",
        "location",
        "experience_required",
        "salary",
        "url",
        "jd_experience_detected",
        "jd_skills",
        "matched_skills",
        "missing_skills",
        "match_percentage",
        "category",
        "relevant_resume_sections",
        "recommendations",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(results)

    print("\n==============================")
    print("ANALYSIS COMPLETED")
    print("==============================")

    print(
        f"\nSaved analysis to: {OUTPUT_FILE}"
    )

    print("\nTop matching jobs:\n")

    for result in results[:10]:

        print(
            f"{result['match_percentage']}% | "
            f"{result['category']} | "
            f"{result['job_title']} | "
            f"{result['company']}"
        )

        print(
            f"Matched: "
            f"{result['matched_skills']}"
        )

        print(
            f"Missing: "
            f"{result['missing_skills']}"
        )

        print("-" * 70)


if __name__ == "__main__":
    main()