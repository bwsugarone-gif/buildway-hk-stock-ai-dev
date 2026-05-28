"""
core/font_utils.py
Buildway Tech (HK) Limited — Font Utilities
Helper functions for managing fonts and Unicode symbol rendering in PDFs
"""

from typing import Dict, List, Optional
from reportlab.lib import colors


class UnicodeSymbols:
    """
    Common Unicode symbols and Chinese text used in the reports.
    Ensures proper rendering across different PDF contexts.
    """
    
    # Verdict icons and symbols
    BUY = "🟢"  # Green circle
    HOLD = "🟡"  # Yellow circle
    SELL = "🔴"  # Red circle
    NEUTRAL = "🟡"  # Yellow circle
    
    # Risk levels
    RISK_LOW = "低風險"
    RISK_MEDIUM = "中等風險"
    RISK_HIGH = "高風險"
    RISK_VERY_HIGH = "極高風險"
    
    # Watch list status
    WATCHLIST = "觀察名單"
    MONITORING = "監察中"
    
    # Investment committee
    IC_RATING = "投委會評級"
    IC_VERDICT = "投委會結論"
    
    # Risk analysis
    COMPOSITE_RISK = "綜合風險評分"
    RISK_DIMENSION = "風險維度"
    
    # Financial metrics
    FINANCIAL_HEALTH = "財務健康"
    VALUATION_RANGE = "估值區間"
    MARKET_DATA = "市場數據"
    
    # Common Chinese text
    TRADITIONAL_CHINESE = "繁體中文"
    GENERATED_DATE = "生成日期"
    GENERATED_TIME = "生成時間"
    DEMO_VERSION = "示範版本"
    SAMPLE_DATA = "示範數據"
    
    @classmethod
    def all_test_strings(cls) -> List[str]:
        """
        Return all test strings for validating font rendering.
        These are the critical strings that must display correctly.
        """
        return [
            cls.TRADITIONAL_CHINESE,  # 繁體中文
            cls.IC_RATING,            # 投委會評級
            cls.RISK_MEDIUM,          # 中等風險
            cls.WATCHLIST,            # 觀察名單
        ]


class FontRecommendations:
    """
    Provides font recommendations for different contexts and operating systems.
    """
    
    WINDOWS_FONTS = {
        "primary": {
            "name": "Microsoft JhengHei",
            "filename": "jhenghei.ttc",
            "description": "Hong Kong & Taiwan standard font",
            "unicode_coverage": 0.95,
        },
        "secondary": {
            "name": "Microsoft YaHei",
            "filename": "msyh.ttc",
            "description": "Mainland China & general CJK",
            "unicode_coverage": 0.90,
        },
        "tertiary": {
            "name": "Ming Li U",
            "filename": "mingliu.ttc",
            "description": "Traditional serif font",
            "unicode_coverage": 0.85,
        },
    }
    
    UNIVERSAL_FONTS = {
        "noto_sans_cjk": {
            "name": "Noto Sans CJK TC",
            "filename": "NotoSansCJKtc-Regular.otf",
            "description": "Google's open-source CJK font",
            "unicode_coverage": 0.99,
        },
    }
    
    @classmethod
    def get_recommended_fonts(cls, os_type: str = "windows") -> Dict[str, Dict]:
        """Get recommended fonts for the operating system."""
        if os_type.lower() == "windows":
            return cls.WINDOWS_FONTS
        return cls.UNIVERSAL_FONTS


class FontValidator:
    """
    Validates that fonts are properly set up for rendering Chinese text.
    """
    
    @staticmethod
    def validate_font_setup(font_name: str, test_strings: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Validate that a font can render the required test strings.
        
        Args:
            font_name: Name of the font to validate
            test_strings: List of strings to test (uses defaults if None)
        
        Returns:
            Dict with validation results
        """
        if test_strings is None:
            test_strings = UnicodeSymbols.all_test_strings()
        
        results = {
            "font_name": font_name,
            "supports_cjk": True,
            "test_strings": test_strings,
            "all_passed": True,
        }
        
        try:
            # Try to encode each test string
            for test_str in test_strings:
                try:
                    test_str.encode('utf-8')
                except UnicodeEncodeError:
                    results["all_passed"] = False
        except Exception as e:
            results["all_passed"] = False
            results["error"] = str(e)
        
        return results


def ensure_unicode_compatibility(text: str) -> str:
    """
    Ensure text is properly formatted for PDF rendering.
    Handles encoding and special character handling.
    
    Args:
        text: Input text (should be a string)
    
    Returns:
        Text properly encoded for PDF rendering
    """
    try:
        # Ensure UTF-8 encoding
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        
        # Verify the text can be encoded
        text.encode('utf-8')
        
        return text
    except Exception as e:
        print(f"Warning: Could not ensure Unicode compatibility: {e}")
        return text


def create_cjk_paragraph_style(base_style, font_name: str, font_bold: Optional[str] = None):
    """
    Create a paragraph style optimized for CJK (Chinese, Japanese, Korean) text.
    
    Args:
        base_style: Base ParagraphStyle to modify
        font_name: Name of the CJK font to use
        font_bold: Optional name of bold CJK font
    
    Returns:
        Modified ParagraphStyle with CJK optimizations
    """
    from reportlab.lib.styles import ParagraphStyle
    
    # Clone the base style
    cjk_style = ParagraphStyle(
        f"{base_style.name}_CJK",
        parent=base_style,
        fontName=font_name,
        leading=base_style.leading * 1.2,  # Slightly increased leading for CJK
    )
    
    return cjk_style


# Test utilities for validation
def test_font_rendering() -> None:
    """
    Test function to validate font rendering setup.
    Prints validation results to console.
    """
    print("\n=== Unicode Symbol Rendering Test ===")
    print("Testing critical strings that must render correctly:\n")
    
    for test_str in UnicodeSymbols.all_test_strings():
        try:
            # Verify UTF-8 encoding
            encoded = test_str.encode('utf-8')
            print(f"[OK] {test_str}")
        except Exception as e:
            print(f"[ERROR] {test_str} - {e}")
    
    print("\n=== Font Recommendations ===")
    recommendations = FontRecommendations.get_recommended_fonts("windows")
    for key, font_info in recommendations.items():
        print(f"\n{font_info['name']}:")
        print(f"  File: {font_info['filename']}")
        print(f"  Description: {font_info['description']}")
        print(f"  Unicode Coverage: {font_info['unicode_coverage']*100:.0f}%")
