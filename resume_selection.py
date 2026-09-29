import csv
import os


ANALYSIS_FILE = "jd_analysis.csv"
OUTPUT_FILE = "selected_jobs.csv"

# Change this later if needed
MIN_MATCH_PERCENTAGE = 55


def main():

    print()
    print("=" * 60)
    print("JOB SELECTION")
    print("=" * 60)
    print()

    if not os.path.exists(ANALYSIS_FILE):
        print(f"ERROR: {ANALYSIS_FILE} not found.")
        print("Run resume_analyzer.py first.")
        return

    with open(
        ANALYSIS_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        jobs = list(csv.DictReader(file))

    selected = []

    for job in jobs:

        try:
            match = float(
                job.get("match_percentage", 0)
            )
        except ValueError:
            match = 0

        title = job.get("job_title", "")
        company = job.get("company", "")
        location = job.get("location", "")

        if match >= MIN_MATCH_PERCENTAGE:

            selected.append(job)

            print(
                f"[SELECTED] {match}% | "
                f"{title} | {company} | {location}"
            )

        else:

            print(
                f"[SKIPPED]  {match}% | "
                f"{title} | {company}"
            )

    # Sort highest match first
    selected.sort(
        key=lambda x: float(
            x.get("match_percentage", 0)
        ),
        reverse=True
    )

    if selected:

        fieldnames = list(
            selected[0].keys()
        )

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
            writer.writerows(selected)

    else:

        print("\nNo jobs passed the selection threshold.")

    print()
    print("=" * 60)
    print("SELECTION COMPLETED")
    print("=" * 60)

    print(
        f"\nTotal jobs analyzed: {len(jobs)}"
    )

    print(
        f"Jobs selected: {len(selected)}"
    )

    print(
        f"Minimum match: {MIN_MATCH_PERCENTAGE}%"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()