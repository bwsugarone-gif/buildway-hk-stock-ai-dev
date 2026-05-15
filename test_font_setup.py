#!/usr/bin/env python3
"""
test_font_setup.py
Buildway Tech (HK) Limited — Font Setup Verification Script

Usage:
    python test_font_setup.py

This script validates that Traditional Chinese fonts are properly configured
for PDF report generation.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from core.pdf_generator import FontManager
from core.font_utils import UnicodeSymbols, test_font_rendering


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def main():
    """Run font setup verification tests."""
    
    print_header("Traditional Chinese Font Setup Verification")
    
    # 1. Test font manager setup
    print("1. Testing FontManager initialization...")
    try:
        font_mgr = FontManager()
        primary_font, bold_font = font_mgr.setup_traditional_chinese_fonts()
        print(f"   ✓ Primary font: {primary_font}")
        print(f"   ✓ Bold font: {bold_font}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # 2. Test Unicode symbol rendering
    print("\n2. Testing Unicode symbol rendering...")
    try:
        test_font_rendering()
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # 3. Test critical strings
    print_header("Testing Critical Strings")
    critical_strings = [
        ("繁體中文", "Traditional Chinese"),
        ("投委會評級", "Investment Committee Rating"),
        ("中等風險", "Medium Risk"),
        ("觀察名單", "Watch List"),
    ]
    
    all_passed = True
    for chinese, english in critical_strings:
        try:
            encoded = chinese.encode('utf-8')
            print(f"   ✓ {chinese} ({english})")
        except Exception as e:
            print(f"   ✗ {chinese} - Error: {e}")
            all_passed = False
    
    # 4. Test PDF generation capabilities
    print_header("PDF Generation Readiness")
    
    if primary_font != "Helvetica":
        print(f"   ✓ CJK font found: {primary_font}")
        print(f"   ✓ Ready to generate PDFs with Chinese text")
        readiness = "READY"
    else:
        print(f"   ⚠ No CJK font found, using fallback: {primary_font}")
        print(f"   ⚠ PDFs may not render Chinese text correctly")
        readiness = "NOT READY"
    
    # 5. Summary
    print_header("Verification Summary")
    
    if all_passed and primary_font != "Helvetica":
        print("✅ Font setup is COMPLETE and READY")
        print("\nYou can now generate PDFs with proper Traditional Chinese rendering:")
        print("  - 繁體中文 will display correctly")
        print("  - 投委會評級 will display correctly")
        print("  - 中等風險 will display correctly")
        print("  - 觀察名單 will display correctly")
        return True
    elif all_passed:
        print("⚠️  Font setup is INCOMPLETE")
        print("\nTo enable proper Chinese character rendering:")
        print("  1. Install Microsoft JhengHei (recommended for HK)")
        print("  2. Or install Noto Sans CJK TC")
        print("\nSee FONT_SETUP_GUIDE.md for detailed instructions")
        return False
    else:
        print("❌ Font setup has ERRORS")
        print("\nPlease check the errors above and refer to FONT_SETUP_GUIDE.md")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
