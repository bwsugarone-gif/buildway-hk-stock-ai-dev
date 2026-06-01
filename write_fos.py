"""
Quarantined legacy patch-writer for FOS components.

This file previously embedded a large HTML/CSS/Python source string and rewrote
core/fos_components.py. It is intentionally disabled before the v4.1.1 merge
gate because the embedded triple-quoted CSS made the script fail Python syntax
checks and the generated component code is now maintained directly.
"""


def main() -> None:
    print("write_fos.py is quarantined; edit core/fos_components.py directly.")


if __name__ == "__main__":
    main()
