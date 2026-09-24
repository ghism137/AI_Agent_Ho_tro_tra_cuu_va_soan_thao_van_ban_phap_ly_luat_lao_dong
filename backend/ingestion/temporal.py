"""Resolve eligibility only from reviewed provision versions and coverage."""

from __future__ import annotations

from datetime import date
from typing import Any


def eligibility(
    version: dict[str, Any], as_of_date: date, *, coverage_verified: bool,
    applicability_resolved: bool, population_matches: bool | None = True,
    transition_resolved: bool = True,
) -> str:
    """Return eligible, ineligible or unknown for one provision version."""
    if (version.get("verification_status") != "verified" or not coverage_verified
            or not applicability_resolved or population_matches is None or not transition_resolved):
        return "unknown"
    if population_matches is False:
        return "ineligible"
    start = version.get("valid_from")
    end = version.get("valid_to")
    if not start:
        return "unknown"
    valid_from = date.fromisoformat(start) if isinstance(start, str) else start
    valid_to = date.fromisoformat(end) if isinstance(end, str) else end
    if valid_to is not None and valid_to <= valid_from:
        raise ValueError("invalid provision interval")
    return "eligible" if valid_from <= as_of_date and (valid_to is None or as_of_date < valid_to) else "ineligible"
