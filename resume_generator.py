import csv
import os
import re
import shutil
from docx import Document
from docx.shared import Pt


# ============================================================
# CONFIG
# ============================================================

MASTER_RESUME = "master_resume/master_resume.docx"
ANALYSIS_FILE = "jd_analysis.csv"
OUTPUT_DIR = "generated_resumes"


# ============================================================
# HELPERS
# ============================================================

def normalize(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def safe_filename(text):
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    text = re.sub(r'\s+', '_', text)
    return text[:100]


def split_skills(text):
    if not text:
        return []

    return [
        item.strip()
        for item in text.split(",")
        if item.strip()
    ]


def paragraph_score(paragraph, matched_skills):
    """
    Score a resume paragraph based on how many JD-matched
    skills appear in it.
    """

    text = normalize(paragraph)
    score = 0

    for skill in matched_skills:
        if normalize(skill) in text:
            score += 1

    return score


# ============================================================
# LOAD MASTER RESUME
# ============================================================

def load_master_resume():

    if not os.path.exists(MASTER_RESUME):
        raise FileNotFoundError(
            f"Master resume not found: {MASTER_RESUME}"
        )

    return Document(MASTER_RESUME)


# ============================================================
# LOAD ANALYSIS
# ============================================================

def load_analysis():

    if not os.path.exists(ANALYSIS_FILE):
        raise FileNotFoundError(
            f"Analysis file not found: {ANALYSIS_FILE}"
        )

    with open(
        ANALYSIS_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        return list(csv.DictReader(file))


# ============================================================
# IDENTIFY SECTIONS
# ============================================================

def identify_sections(document):

    sections = []

    current_section = "General"

    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if not text:
            continue

        lower = normalize(text)

        # Common resume headings
        if any(
            heading in lower
            for heading in [
                "summary",
                "professional summary",
                "profile",
                "skills",
                "technical skills",
                "experience",
                "professional experience",
                "work experience",
                "projects",
                "education",
                "certification",
                "certifications",
            ]
        ) and len(text) < 60:

            current_section = text

        sections.append({
            "section": current_section,
            "text": text,
            "style": paragraph.style.name
        })

    return sections


# ============================================================
# FIND RELEVANT CONTENT
# ============================================================

def find_relevant_content(sections, matched_skills):

    scored = []

    for item in sections:

        score = paragraph_score(
            item["text"],
            matched_skills
        )

        scored.append({
            "section": item["section"],
            "text": item["text"],
            "score": score
        })

    return scored


# ============================================================
# CREATE TARGETED RESUME
# ============================================================

def create_targeted_resume(
    master_document,
    analysis
):

    job_title = analysis.get(
        "job_title",
        "DevOps Engineer"
    )

    company = analysis.get(
        "company",
        ""
    )

    location = analysis.get(
        "location",
        ""
    )

    matched_skills = split_skills(
        analysis.get(
            "matched_skills",
            ""
        )
    )

    jd_skills = split_skills(
        analysis.get(
            "jd_skills",
            ""
        )
    )

    missing_skills = split_skills(
        analysis.get(
            "missing_skills",
            ""
        )
    )

    match_percentage = analysis.get(
        "match_percentage",
        "0"
    )

    # Analyze master resume
    sections = identify_sections(
        master_document
    )

    scored_content = find_relevant_content(
        sections,
        matched_skills
    )

    # Sort by relevance
    relevant_content = sorted(
        scored_content,
        key=lambda x: x["score"],
        reverse=True
    )

    # Create new document
    doc = Document()

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = doc.add_paragraph()

    run = title.add_run(
        "Targeted Resume"
    )

    run.bold = True
    run.font.size = Pt(18)

    # --------------------------------------------------------
    # TARGET INFORMATION
    # --------------------------------------------------------

    p = doc.add_paragraph()

    run = p.add_run(
        f"Target Role: {job_title}"
    )

    run.bold = True

    doc.add_paragraph(
        f"Company: {company}"
    )

    if location:
        doc.add_paragraph(
            f"Location: {location}"
        )

    doc.add_paragraph(
        f"JD Match: {match_percentage}%"
    )

    # --------------------------------------------------------
    # TARGETED SKILLS
    # --------------------------------------------------------

    doc.add_heading(
        "Targeted Technical Skills",
        level=1
    )

    if matched_skills:

        doc.add_paragraph(
            ", ".join(matched_skills)
        )

    else:

        doc.add_paragraph(
            "No directly matched skills identified."
        )

    # --------------------------------------------------------
    # IMPORTANT NOTE
    # --------------------------------------------------------

    note = doc.add_paragraph()

    run = note.add_run(
        "Resume targeting is based only on information "
        "already present in the master resume. Missing "
        "JD requirements are not added as qualifications."
    )

    run.italic = True

    # --------------------------------------------------------
    # RELEVANT EXPERIENCE
    # --------------------------------------------------------

    doc.add_heading(
        "Most Relevant Experience",
        level=1
    )

    relevant_experience = [
        item
        for item in relevant_content
        if item["score"] >= 1
        and any(
            keyword in normalize(item["section"])
            for keyword in [
                "experience",
                "work",
                "professional"
            ]
        )
    ]

    used = set()

    for item in relevant_experience:

        text = item["text"]

        if text in used:
            continue

        used.add(text)

        paragraph = doc.add_paragraph(
            style="List Bullet"
        )

        paragraph.add_run(text)

        if len(used) >= 12:
            break

    if not relevant_experience:

        doc.add_paragraph(
            "No experience bullets directly matched "
            "the detected JD skills."
        )

    # --------------------------------------------------------
    # RELEVANT PROJECTS
    # --------------------------------------------------------

    doc.add_heading(
        "Most Relevant Projects",
        level=1
    )

    relevant_projects = [
        item
        for item in relevant_content
        if "project" in normalize(item["section"])
    ]

    used_projects = set()

    for item in relevant_projects:

        text = item["text"]

        if text in used_projects:
            continue

        used_projects.add(text)

        paragraph = doc.add_paragraph(
            style="List Bullet"
        )

        paragraph.add_run(text)

        if len(used_projects) >= 10:
            break

    if not relevant_projects:

        doc.add_paragraph(
            "No project content directly matched "
            "the detected JD skills."
        )

    # --------------------------------------------------------
    # ORIGINAL RESUME CONTENT
    # --------------------------------------------------------

    doc.add_heading(
        "Additional Resume Content",
        level=1
    )

    # Keep remaining useful content,
    # but don't duplicate content already shown.
    displayed = used | used_projects

    for item in sections:

        text = item["text"]

        if text in displayed:
            continue

        # Don't repeat headings that have already
        # been represented by our generated sections.
        lower = normalize(text)

        if lower in [
            "summary",
            "professional summary",
            "profile",
            "technical skills",
            "skills",
            "experience",
            "professional experience",
            "work experience",
            "projects",
            "education",
            "certifications",
            "certification",
        ]:
            continue

        paragraph = doc.add_paragraph()

        paragraph.add_run(text)

    # --------------------------------------------------------
    # JD GAP INFORMATION
    # --------------------------------------------------------

    doc.add_heading(
        "JD Gap Review",
        level=1
    )

    if missing_skills:

        doc.add_paragraph(
            "The following JD skills were detected but "
            "were not found in the master resume:"
        )

        for skill in missing_skills:

            doc.add_paragraph(
                skill,
                style="List Bullet"
            )

    else:

        doc.add_paragraph(
            "No detected JD skills were missing from "
            "the master resume."
        )

    # --------------------------------------------------------
    # JD REFERENCE
    # --------------------------------------------------------

    doc.add_heading(
        "Targeting Summary",
        level=1
    )

    doc.add_paragraph(
        f"Target role: {job_title}"
    )

    doc.add_paragraph(
        f"Company: {company}"
    )

    doc.add_paragraph(
        f"Matched skills: "
        f"{', '.join(matched_skills)}"
    )

    doc.add_paragraph(
        f"JD skills detected: "
        f"{', '.join(jd_skills)}"
    )

    # --------------------------------------------------------
    # FORMAT
    # --------------------------------------------------------

    for paragraph in doc.paragraphs:

        for run in paragraph.runs:

            run.font.name = "Arial"
            run.font.size = Pt(10)

    return doc


# ============================================================
# CLEAN OUTPUT DIRECTORY
# ============================================================

def clean_output_directory():

    if os.path.exists(OUTPUT_DIR):

        print("Cleaning old generated resumes...")

        for filename in os.listdir(OUTPUT_DIR):

            file_path = os.path.join(
                OUTPUT_DIR,
                filename
            )

            try:

                if os.path.isfile(file_path):
                    os.remove(file_path)

                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)

            except Exception as error:

                print(
                    f"Could not remove {file_path}: {error}"
                )

    else:

        os.makedirs(OUTPUT_DIR)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("JD-SPECIFIC RESUME GENERATOR")
    print("=" * 60)
    print()

    # Clean previous generated resumes
    clean_output_directory()

    master_document = load_master_resume()

    analyses = load_analysis()

    print(
        f"Loaded {len(analyses)} analyzed jobs."
    )

    print()

    generated = 0

    for index, analysis in enumerate(
        analyses,
        start=1
    ):

        job_title = analysis.get(
            "job_title",
            "DevOps Engineer"
        )

        company = analysis.get(
            "company",
            "Company"
        )

        print(
            f"[{index}/{len(analyses)}] "
            f"{job_title} - {company}"
        )

        try:

            document = create_targeted_resume(
                master_document,
                analysis
            )

            # ------------------------------------------------
            # UNIQUE JOB-SPECIFIC FILENAME
            # ------------------------------------------------

            filename = (
                f"{index:03d}_"
                f"{safe_filename(company)}_"
                f"{safe_filename(job_title)}.docx"
            )

            output_path = os.path.join(
                OUTPUT_DIR,
                filename
            )

            document.save(
                output_path
            )

            generated += 1

            print(
                f"    Created: {filename}"
            )

        except Exception as error:

            print(
                f"    ERROR: {error}"
            )

    print()
    print("=" * 60)
    print("GENERATION COMPLETED")
    print("=" * 60)

    print(
        f"\nGenerated resumes: {generated}"
    )

    print(
        f"Output folder: {OUTPUT_DIR}"
    )


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()