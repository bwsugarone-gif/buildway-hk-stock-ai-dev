# Traditional Chinese PDF Rendering Guide

## Overview

This document explains how to properly set up Traditional Chinese font support for PDF report generation in the Buildway HK Stock AI project.

## Current Implementation

The PDF generator now includes a robust `FontManager` class that:
- ✅ Automatically searches for Traditional Chinese fonts
- ✅ Tries multiple font sources in priority order
- ✅ Falls back gracefully if no CJK fonts are found
- ✅ Applies fonts consistently across all PDF sections
- ✅ Supports Unicode symbols and special characters

## Required Text Rendering

All PDFs must correctly display:
- `繁體中文` (Traditional Chinese)
- `投委會評級` (Investment Committee Rating)
- `中等風險` (Medium Risk)
- `觀察名單` (Watch List)
- Unicode symbols and icons

## Font Search Priority

The system searches for fonts in this order on Windows:

### 1. **Microsoft JhengHei** (Recommended for Hong Kong)
- File: `jhenghei.ttc` or `jhenghei.ttf`
- Location: `C:\Windows\Fonts\`
- Unicode Coverage: 95%+
- **Best choice for Hong Kong stocks**

### 2. **Microsoft YaHei**
- File: `msyh.ttc` or `msyh.ttf`
- Location: `C:\Windows\Fonts\`
- Unicode Coverage: 90%+
- Good general-purpose CJK font

### 3. **Ming Li U**
- File: `mingliu.ttc` or `mingliu.ttf`
- Location: `C:\Windows\Fonts\`
- Unicode Coverage: 85%+
- Traditional serif font for Traditional Chinese

### 4. **Noto Sans CJK TC** (Universal)
- File: `NotoSansCJKtc-Regular.otf`
- Available across Windows/Mac/Linux
- Unicode Coverage: 99%+
- Install from: https://www.google.com/get/noto/

### 5. **Project Fonts Directory**
- Location: `buildway-hk-stock-ai/assets/fonts/`
- Add custom font files here for bundled deployment

## Installation Guide

### Windows

Most Windows installations include Microsoft JhengHei or YaHei. To verify:

1. Open `C:\Windows\Fonts\`
2. Look for:
   - `jhenghei.ttc` (Microsoft JhengHei)
   - `msyh.ttc` (Microsoft YaHei)
   - `mingliu.ttc` (Ming Li U)

If not found, download from:
- Microsoft Office installation includes these fonts
- Windows Language Pack for Chinese (Traditional)

### Mac

Install via Homebrew:
```bash
brew install font-noto-sans-cjk
```

Or download manually:
- Download from: https://www.google.com/get/noto/
- Extract to: `~/Library/Fonts/`

### Linux

Install via package manager:
```bash
# Ubuntu/Debian
sudo apt-get install fonts-noto-cjk

# Fedora
sudo dnf install google-noto-sans-cjk-fonts

# Arch
sudo pacman -S noto-fonts-cjk
```

## Verification

To verify the font setup is working:

1. Run the PDF generator
2. Check the console output for font registration messages
3. Look for output like:
   ```
   === Traditional Chinese Font Setup ===
   ✓ Font registered: Microsoft JhengHei (jhenghei.ttc)
   ✓ Primary font set to: Microsoft JhengHei
   ✓ Successfully registered fonts for: 繁體中文, 投委會評級, 中等風險, 觀察名單
   ```

4. Check the generated PDF:
   - Chinese characters should display properly (not as boxes)
   - All text in the test strings should render correctly

## Troubleshooting

### Issue: Chinese characters appear as boxes (□)

**Cause**: No compatible fonts found
**Solution**:
1. Verify a font is installed (see Installation Guide above)
2. Check console output for font registration errors
3. Reinstall Microsoft Office or Language Pack
4. Install Noto Sans CJK TC as fallback

### Issue: Font registration errors in console

**Example**: `✗ Failed to register Microsoft JhengHei: [error details]`

**Solutions**:
1. Check font file exists: `dir C:\Windows\Fonts\jhenghei.ttc`
2. Verify read permissions on the font file
3. Try alternative fonts (see font search priority above)
4. Reinstall Windows Language Pack

### Issue: PDF generation is slow

**Cause**: Font file not found, trying all fallbacks
**Solution**:
1. Install the recommended font (Microsoft JhengHei)
2. Place font files in `assets/fonts/` for faster loading

### Issue: Only English text displays, no Chinese

**Cause**: Font not properly registered or text not encoded as UTF-8
**Solution**:
1. Check font registration (see Verification section)
2. Ensure all text data is UTF-8 encoded
3. Check PDF file permissions

## Code Usage

### Basic Usage

The `PDFGenerator` class handles font setup automatically:

```python
from core.pdf_generator import PDFGenerator

# Font setup happens automatically in __init__
pdf_gen = PDFGenerator(logo_path="path/to/logo.png")

# Generate PDF with proper Chinese font support
pdf_gen.generate(report_sections, output_path="report.pdf")
```

### Manual Font Testing

To test font rendering:

```python
from core.font_utils import UnicodeSymbols, test_font_rendering

# Test all required strings
test_font_rendering()

# Validate specific text
test_strings = UnicodeSymbols.all_test_strings()
print("Test strings:", test_strings)
```

### Using FontManager Directly

```python
from core.pdf_generator import FontManager

font_mgr = FontManager()
primary_font, bold_font = font_mgr.setup_traditional_chinese_fonts()

# primary_font will be a registered font name like "MicrosoftJhengHei"
# Use in your reportlab styles
```

## Performance Considerations

1. **Font Loading**: First PDF generation may take slightly longer (font registration overhead)
2. **Subsequent PDFs**: Faster (fonts already registered)
3. **Font Path Search**: Automatic, checks multiple locations
4. **Fallback Handling**: Graceful degradation if fonts not found

## Font Files for Bundled Deployment

To bundle fonts with your application:

1. Create directory: `buildway-hk-stock-ai/assets/fonts/`
2. Place font files there:
   - `jhenghei.ttc` (Microsoft JhengHei)
   - `NotoSansCJKtc-Regular.otf` (Noto Sans CJK TC)
3. The `FontManager` will automatically find and use these

**Note**: Ensure you have proper font licensing for distribution.

## Font Coverage Matrix

| Font | CJK | Unicode Symbols | Emojis | Size |
|------|-----|-----------------|--------|------|
| Microsoft JhengHei | ✅ | ✅ | ⚠️ | ~10MB |
| Microsoft YaHei | ✅ | ✅ | ⚠️ | ~10MB |
| Ming Li U | ✅ | ✅ | ❌ | ~8MB |
| Noto Sans CJK TC | ✅ | ✅ | ✅ | ~20MB |

## Unicode Symbols Test

Critical strings that must render correctly:
- `繁體中文` - Traditional Chinese text
- `投委會評級` - Investment Committee Rating
- `中等風險` - Medium Risk level
- `觀察名單` - Watch List status

All of these use standard Unicode characters supported by modern CJK fonts.

## References

- [ReportLab Font Documentation](https://www.reportlab.com/docs/reportlab-fonts.pdf)
- [Google Noto Fonts CJK](https://www.google.com/get/noto/#sans-cjk)
- [Unicode CJK Unified Ideographs](https://unicode.org/charts/PDF/U4E00.pdf)
- [Microsoft Font List](https://docs.microsoft.com/en-us/typography/fonts/windows_10_font_list)

## Support

For font-related issues:
1. Check the console output for `=== Traditional Chinese Font Setup ===` section
2. Verify fonts are installed per Installation Guide
3. Review Troubleshooting section above
4. Check that PDF files have proper UTF-8 encoding

---

**Last Updated**: May 2026
**Project**: Buildway HK Stock AI
**Version**: 1.0
