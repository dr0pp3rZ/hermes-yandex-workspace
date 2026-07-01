#!/usr/bin/env python3
"""_hermes_home.py — Resolve HERMES_HOME consistently across all scripts."""

from pathlib import Path


def get_hermes_home() -> Path:
    """Return the Hermes home directory (~/.hermes)."""
    return Path.home() / ".hermes"


def display_hermes_home() -> str:
    """Return a user-friendly display path for HERMES_HOME."""
    return "~/.hermes"
