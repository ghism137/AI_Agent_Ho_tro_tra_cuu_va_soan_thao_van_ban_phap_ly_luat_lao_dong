"""Permanently retired unsafe metadata-review generator.

The former script emitted verified decisions from hard-coded values and a
``2020-01-01`` fallback. Its output is retained only in
``data/registry/reviews/archive/`` for audit history. Importing this module is
safe; executing it always fails before reading or writing project data.
"""

from __future__ import annotations


def main() -> None:
    raise RuntimeError(
        "retired_auto_metadata_review is permanently disabled; create "
        "source-grounded review proposals and obtain an actual reviewer decision"
    )


if __name__ == "__main__":
    main()
