"""
core/__init__.py
Buildway Tech (HK) Limited — Core Package
"""

# Font utilities for Traditional Chinese support
from .font_utils import (
    UnicodeSymbols,
    FontRecommendations,
    FontValidator,
    ensure_unicode_compatibility,
    test_font_rendering,
)

# PDF generation with Chinese font support
from .pdf_generator import PDFGenerator, FontManager

__all__ = [
    'UnicodeSymbols',
    'FontRecommendations', 
    'FontValidator',
    'ensure_unicode_compatibility',
    'test_font_rendering',
    'PDFGenerator',
    'FontManager',
]
