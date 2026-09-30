import pandas as pd
import os


# ============================================================
# CONFIG
# ============================================================

SELECTED_JOBS_FILE = "selected_jobs.csv"
OUTPUT_FILE = "application_tracker.csv"
RESUME_DIR = "generated_resumes"


# ============================================================
# LOAD SELECTED JOBS
# ============================================================

df = pd.read_csv(SELECTED_JOBS_FILE)

print("=" * 60)
print("APPLICATION TRACKER GENERATOR")
print("=" * 60)
print()

print(f"Selected jobs found: {len(df)}")


# ============================================================
# CREATE TRACKER
# ============================================================

tracker = pd.DataFrame()

tracker["job_id"] = [
    f"{i:03d}"
    for i in range(1, len(df) + 1)
]

tracker["job_title"] = df["job_title"]
tracker["company"] = df["company"]
tracker["location"] = df["location"]
tracker["experience_required"] = df["experience_required"]
tracker["salary"] = df["salary"]
tracker["url"] = df["url"]
tracker["match_percentage"] = df["match_percentage"]
tracker["matched_skills"] = df["matched_skills"]
tracker["missing_skills"] = df["missing_skills"]
tracker["category"] = df["category"]


# ============================================================
# MAP RESUMES
# ============================================================

resume_files = []

for i in range(1, len(df) + 1):

    prefix = f"{i:03d}_"

    matching_files = [
        filename
        for filename in os.listdir(RESUME_DIR)
        if filename.startswith(prefix)
        and filename.lower().endswith(".docx")
    ]

    if matching_files:
        resume_files.append(
            os.path.join(
                RESUME_DIR,
                matching_files[0]
            )
        )
    else:
        resume_files.append("")


tracker["resume_file"] = resume_files


# ============================================================
# APPLICATION STATUS
# ============================================================

tracker["application_status"] = "Not Applied"

tracker["applied_date"] = ""

tracker["application_notes"] = ""


# ============================================================
# SAVE
# ============================================================

tracker.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# VALIDATION
# ============================================================

print()

print(f"Tracker created: {OUTPUT_FILE}")

print(
    f"Total jobs: {len(tracker)}"
)

print(
    f"Jobs with resumes: "
    f"{tracker['resume_file'].ne('').sum()}"
)

print(
    f"Jobs without resumes: "
    f"{tracker['resume_file'].eq('').sum()}"
)

print()

print("=" * 60)
print("APPLICATION TRACKER READY")
print("=" * 60)

print()

print(
    tracker[
        [
            "job_id",
            "job_title",
            "company",
            "resume_file",
            "application_status"
        ]
    ].to_string(index=False)
)