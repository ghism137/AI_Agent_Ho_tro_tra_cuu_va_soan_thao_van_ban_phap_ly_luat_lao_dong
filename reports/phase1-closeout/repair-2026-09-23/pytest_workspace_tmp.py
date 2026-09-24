"""Pytest evidence plugin for hosts whose system temp root is inaccessible.

This overrides only ``tmp_path`` and creates a fresh directory below the
writable repository ``tmp`` directory for each requesting test.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest


@pytest.fixture
def tmp_path(request: pytest.FixtureRequest):
    root = Path.cwd() / "tmp" / f"pytest-workspace-{os.getpid()}"
    root.mkdir(parents=True, exist_ok=True)
    prefix = hashlib.sha256(request.node.nodeid.encode("utf-8")).hexdigest()[:12]
    path = root / prefix
    path.mkdir()
    return path
