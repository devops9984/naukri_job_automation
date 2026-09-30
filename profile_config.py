# ============================================================
# USER APPLICATION PROFILE CONFIGURATION
# ============================================================

# ------------------------------------------------------------
# JOINING / AVAILABILITY
# ------------------------------------------------------------

NOTICE_PERIOD = "Immediate"


# ------------------------------------------------------------
# CITIZENSHIP
# ------------------------------------------------------------

CITIZENSHIP = "Indian"

COUNTRY_OF_CITIZENSHIP = "India"


# ------------------------------------------------------------
# SKILL EXPERIENCE
# ------------------------------------------------------------

# Calculate skill experience from documented employment periods
# and skill mentions in the resume.
CALCULATE_SKILL_EXPERIENCE = True


# ------------------------------------------------------------
# UNKNOWN ANSWERS
# ------------------------------------------------------------

# Never guess an answer that is not supported by:
#
# 1. Verified application answer
# 2. Naukri profile
# 3. Master resume
# 4. Configured rule
#
# Unknown questions should be marked for review.

UNKNOWN_ANSWER = "REVIEW_REQUIRED"


# ------------------------------------------------------------
# WORK AUTHORIZATION
# ------------------------------------------------------------

# Keep this separate from citizenship.
#
# Example:
# "Are you authorized to work in the US?"
#
# should NOT automatically be answered from CITIZENSHIP.

WORK_AUTHORIZATION = None


# ------------------------------------------------------------
# SPONSORSHIP
# ------------------------------------------------------------

# Keep this empty until explicitly configured.

REQUIRES_SPONSORSHIP = None


# ------------------------------------------------------------
# SALARY
# ------------------------------------------------------------

# Leave empty until you explicitly configure the value.

EXPECTED_SALARY = None


# ------------------------------------------------------------
# RELOCATION
# ------------------------------------------------------------

# Leave empty until explicitly configured.

WILLING_TO_RELOCATE = None