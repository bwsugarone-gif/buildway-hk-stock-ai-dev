"""
scripts/check_runtime.py
Python Runtime Lock Check — Buildway HK Stock AI

This project is pinned to Python 3.11.
Run this script before any QA to confirm the correct interpreter is active.

Usage:
    python scripts/check_runtime.py
    py -3.11 scripts/check_runtime.py
"""

import sys

REQUIRED_MAJOR = 3
REQUIRED_MINOR = 11

def check():
    major = sys.version_info.major
    minor = sys.version_info.minor
    patch = sys.version_info.micro
    exe   = sys.executable

    print(f"Python executable : {exe}")
    print(f"Python version    : {major}.{minor}.{patch}")

    if major != REQUIRED_MAJOR or minor != REQUIRED_MINOR:
        print()
        print("=" * 60)
        print(f"❌ RUNTIME LOCK FAIL")
        print(f"   Required : Python {REQUIRED_MAJOR}.{REQUIRED_MINOR}.x")
        print(f"   Found    : Python {major}.{minor}.{patch}")
        print()
        print("   This project is pinned to Python 3.11.")
        print("   Do NOT use Python 3.12 / 3.13 / 3.14 unless")
        print("   explicitly approved by the project owner.")
        print()
        print("   On Windows, use:  py -3.11 <script.py>")
        print("   Or activate the correct .venv built with Python 3.11.")
        print("=" * 60)
        sys.exit(1)

    print()
    print("=" * 60)
    print(f"✅ RUNTIME LOCK PASS — Python {major}.{minor}.{patch}")
    print("=" * 60)


if __name__ == "__main__":
    check()
