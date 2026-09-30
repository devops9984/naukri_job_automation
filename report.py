import os
import pandas as pd


TRACKER_FILE = "application_tracker.csv"
REPORT_FILE = "application_report.csv"


def main():

    # =========================================================
    # CHECK TRACKER FILE
    # =========================================================

    if not os.path.exists(TRACKER_FILE):
        print()
        print("=" * 70)
        print("ERROR")
        print("=" * 70)
        print(f"{TRACKER_FILE} was not found.")
        print("Make sure report.py is inside your naukri_job_automation folder.")
        print("=" * 70)
        return

    # =========================================================
    # LOAD TRACKER
    # =========================================================

    try:
        df = pd.read_csv(TRACKER_FILE)
    except Exception as e:
        print()
        print("ERROR: Could not read application_tracker.csv")
        print(f"Details: {e}")
        return

    # Clean column names
    df.columns = [str(col).strip() for col in df.columns]

    # Check required column
    if "application_status" not in df.columns:
        print()
        print("ERROR: application_status column not found.")
        print()
        print("Available columns:")
        print(list(df.columns))
        return

    # =========================================================
    # CLEAN STATUS
    # =========================================================

    df["application_status"] = (
        df["application_status"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    # =========================================================
    # CLASSIFY JOBS
    # =========================================================

    status_lower = df["application_status"].str.lower()

    applied = df[
        status_lower == "applied"
    ]

    external = df[
        status_lower == "external site"
    ]

    review = df[
        status_lower == "review required"
    ]

    other = df[
        ~status_lower.isin(
            [
                "applied",
                "external site",
                "review required"
            ]
        )
    ]

    total = len(df)

    # =========================================================
    # HEADER
    # =========================================================

    print()
    print("=" * 70)
    print("                 NAUKRI APPLICATION REPORT")
    print("=" * 70)

    print()
    print(f"Total Jobs Processed       : {total}")
    print(f"Successfully Applied       : {len(applied)}")
    print(f"External Company Site      : {len(external)}")
    print(f"Review Required / Not Done : {len(review)}")

    if len(other) > 0:
        print(f"Other / Unknown            : {len(other)}")

    print("-" * 70)

    # =========================================================
    # SUCCESSFULLY APPLIED
    # =========================================================

    print()
    print("SUCCESSFULLY APPLIED")
    print("-" * 70)

    if len(applied) == 0:

        print("None")

    else:

        for _, row in applied.iterrows():

            job_id = row.get("job_id", "")
            title = row.get("job_title", "")
            company = row.get("company", "")
            applied_date = row.get("applied_date", "")

            print()
            print(
                f"{job_id} | {title} | {company}"
            )

            print("    Status  : SUCCESSFUL")
            print(
                "    Message : Application successfully submitted on Naukri."
            )

            if pd.notna(applied_date) and str(applied_date).strip():
                print(
                    f"    Date    : {applied_date}"
                )

    # =========================================================
    # EXTERNAL COMPANY SITE
    # =========================================================

    print()
    print("EXTERNAL COMPANY SITE")
    print("-" * 70)

    if len(external) == 0:

        print("None")

    else:

        for _, row in external.iterrows():

            job_id = row.get("job_id", "")
            title = row.get("job_title", "")
            company = row.get("company", "")
            notes = row.get("application_notes", "")
            url = row.get("url", "")

            print()
            print(
                f"{job_id} | {title} | {company}"
            )

            print("    Status  : NOT APPLIED ON NAUKRI")
            print(
                "    Reason  : Application requires the company's website."
            )

            if pd.notna(notes) and str(notes).strip():
                print(
                    f"    Details : {notes}"
                )

            if pd.notna(url) and str(url).strip():
                print(
                    f"    URL     : {url}"
                )

    # =========================================================
    # REVIEW REQUIRED
    # =========================================================

    print()
    print("REVIEW REQUIRED / NOT COMPLETED")
    print("-" * 70)

    if len(review) == 0:

        print("None")

    else:

        for _, row in review.iterrows():

            job_id = row.get("job_id", "")
            title = row.get("job_title", "")
            company = row.get("company", "")
            notes = row.get("application_notes", "")
            url = row.get("url", "")

            print()
            print(
                f"{job_id} | {title} | {company}"
            )

            print("    Status : NOT APPLIED")

            if pd.notna(notes) and str(notes).strip():

                print(
                    f"    Reason : {notes}"
                )

            else:

                print(
                    "    Reason : Automation could not safely complete the application."
                )

            if pd.notna(url) and str(url).strip():

                print(
                    f"    URL    : {url}"
                )

    # =========================================================
    # OTHER / UNKNOWN
    # =========================================================

    if len(other) > 0:

        print()
        print("OTHER / UNKNOWN STATUS")
        print("-" * 70)

        for _, row in other.iterrows():

            job_id = row.get("job_id", "")
            title = row.get("job_title", "")
            company = row.get("company", "")
            status = row.get("application_status", "")
            notes = row.get("application_notes", "")

            print()
            print(
                f"{job_id} | {title} | {company}"
            )

            print(
                f"    Status : {status}"
            )

            if pd.notna(notes) and str(notes).strip():

                print(
                    f"    Details: {notes}"
                )

    # =========================================================
    # SAVE DETAILED REPORT
    # =========================================================

    report_columns = [
        "job_id",
        "job_title",
        "company",
        "location",
        "experience_required",
        "salary",
        "url",
        "match_percentage",
        "matched_skills",
        "missing_skills",
        "category",
        "resume_file",
        "application_status",
        "applied_date",
        "application_notes",
    ]

    available_columns = [
        column
        for column in report_columns
        if column in df.columns
    ]

    report_df = df[available_columns].copy()

    # Add a clear report status
    def get_report_status(status):

        status = str(status).strip().lower()

        if status == "applied":
            return "SUCCESSFUL"

        elif status == "external site":
            return "NOT APPLIED ON NAUKRI"

        elif status == "review required":
            return "NOT APPLIED"

        else:
            return "UNKNOWN"

    report_df["report_status"] = (
        report_df["application_status"]
        .apply(get_report_status)
    )

    # Put report_status next to application_status
    columns = list(report_df.columns)

    if "report_status" in columns:
        columns.remove("report_status")

        if "application_status" in columns:
            index = columns.index("application_status") + 1
            columns.insert(index, "report_status")
        else:
            columns.append("report_status")

        report_df = report_df[columns]

    # Save CSV
    try:

        report_df.to_csv(
            REPORT_FILE,
            index=False,
            encoding="utf-8-sig"
        )

    except Exception as e:

        print()
        print("ERROR: Could not save application report.")
        print(f"Details: {e}")
        return

    # =========================================================
    # VERIFICATION
    # =========================================================

    counted = (
        len(applied)
        + len(external)
        + len(review)
        + len(other)
    )

    print()
    print("=" * 70)
    print("REPORT SUMMARY")
    print("=" * 70)

    print(
        f"Total                  : {total}"
    )

    print(
        f"Successful             : {len(applied)}"
    )

    print(
        f"External Site          : {len(external)}"
    )

    print(
        f"Review Required        : {len(review)}"
    )

    if len(other) > 0:

        print(
            f"Unknown                : {len(other)}"
        )

    print(
        f"Total Accounted For    : {counted}"
    )

    if counted == total:

        print()
        print("VERIFICATION: PASSED")
        print("All processed jobs are accounted for.")

    else:

        print()
        print("VERIFICATION: FAILED")
        print("The status count does not match the total jobs.")

    # =========================================================
    # REPORT FILE
    # =========================================================

    print()
    print("=" * 70)
    print("REPORT GENERATED SUCCESSFULLY")
    print("=" * 70)

    print(
        f"File: {REPORT_FILE}"
    )

    print()
    print("You can open application_report.csv in Excel.")
    print("=" * 70)


if __name__ == "__main__":
    main()