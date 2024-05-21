# tasks.py

from celery import shared_task
from .models import AgencyBranch
import re


@shared_task
def perform_sql_validation(agency_branch_id):
    """
    Task to perform SQL validation on an agency branch.
    """
    # Retrieve the AgencyBranch instance
    agency_branch = AgencyBranch.objects.get(id=agency_branch_id)

    # Get the agency name
    agency_name = agency_branch.List_office_name

    # Handle Keller Williams specific transformation
    agency_name = re.sub(
        r"(?i)kw(\s+|-)*keller(\s+and\s+)?a\s+w\s*kw|(\s+|-)*kw(\s+|-)*keller(\s+and\s+)?a\s+w|(\s+|-)*kw(\s+|-)*keller(\s+and\s+)?a\s+w(\s+|-)*kw|(\s+|-)*keller(\s+and\s+)?a\s+wk",
        "Keller Williams",
        agency_name,
    )

    # SQL query patterns and replacements
    sql_patterns_replacements = [
        ("%keller%williams%", "Keller Williams"),  # Handling for Keller Williams
        (r"(?i)^[ |\-]*", ""),  # Remove leading spaces/hyphens
        ("%cold%well%|cb%", "Coldwell Banker"),
        ("%berkshire%|BHHS%", "BHHS"),
        ("%century%21%|c21%|c_21%", "Century 21"),
        (r"exp[- ]", "eXp Realty"),
        ("%sotheby%", "Sotheby's"),
        ("homesmart%", "HomeSmart"),
        ("%weichert%", "Weichert"),
        ("%long%foster%", "Long & Foster"),
        ("%charl%rutenb%", "Charles Rutenberg Realty"),
        ("%howard%hanna%", "Howard Hanna"),
        ("%exit%realty%", "Exit Realty"),
        ("%douglas%ellim%", "Douglas Elliman"),
        ("engel%lkers%|%volker%|%voelkers%", "Engel & Volkers"),
        ("%keyes%comp%", "The Keyes Company"),
        ("%redfin%", "Redfin"),
        ("%fathom%", "Fathom Realty"),
        (r"(?i),(llc|inc|l\.l\.c\.|ltd)$", ""),
        (r"(?i) (llc|inc|l\.l\.c\.|ltd)$", ""),
        (r"(?i) (re|ll|[a-z0-9])$", ""),
        (r"(?i) ([,!\.])$", ""),
        (r"(?i)/(broker|realtor)", ""),
        (r"u[0-9a-z]{4}", ""),  # New replacement from provided SQL
        (r"\\u0%", ""),  # New replacement from provided SQL
    ]

    # Apply each pattern and replacement to the agency name
    for pattern, replacement in sql_patterns_replacements:
        agency_name = re.sub(pattern, replacement, agency_name, flags=re.IGNORECASE)

    # Update the agency name in the AgencyBranch instance
    agency_branch.List_office_name = agency_name
    agency_branch.save()
