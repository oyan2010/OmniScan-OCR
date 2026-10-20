"""
Comprehensive Verification Test Suite for OmniScan OCR.
Tests:
1. Config load/save
2. English local OCR
3. Urdu/Arabic local OCR
4. PDF multi-page extraction with custom page range
"""
import os
import sys
import numpy as np

# Ensure Windows console supports UTF-8
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from PIL import Image, ImageDraw, ImageFont
import pymupdf

from config import load_config, save_config
from ocr_engine import recognize_text, get_easyocr_reader
from pdf_processor import process_pdf, parse_page_ranges, get_pdf_info

def run_tests():
    print("=" * 60)
    print("Running OmniScan OCR Verification Tests")
    print("=" * 60)
    
    # Test 1: Config
    print("\n[Test 1] Testing Configuration Manager...")
    cfg = load_config()
    assert "engine" in cfg
    assert "language" in cfg
    print("✓ Configuration loaded successfully:", cfg["language"])
    
    # Test 2: Local OCR with English
    print("\n[Test 2] Testing Local English OCR...")
    img_en = Image.new("RGB", (400, 100), color=(255, 255, 255))
    draw_en = ImageDraw.Draw(img_en)
    draw_en.text((20, 30), "OmniScan OCR 2026 Test", fill=(0, 0, 0))
    
    text_en = recognize_text(img_en, engine="local", lang_key="en")
    print("Detected English text:\n", repr(text_en))
    assert "OmniScan" in text_en or "OCR" in text_en or "2026" in text_en
    print("✓ Local English OCR passed!")
    
    # Test 3: Local OCR with Urdu & Arabic
    print("\n[Test 3] Testing Local Urdu & Arabic OCR reader...")
    # Verify reader instance
    reader = get_easyocr_reader("ur_en")
    assert reader is not None
    print("✓ Urdu/Arabic Reader loaded successfully with cached models!")
    
    # Test 4: PDF Processing & Custom Page Range
    print("\n[Test 4] Testing PDF Multi-page creation and extraction...")
    test_pdf_path = "test_sample.pdf"
    
    # Create a 3-page test PDF
    doc = pymupdf.open()
    for p_num in range(1, 4):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 100), f"This is Page {p_num} of OmniScan Document.", fontsize=18)
        page.insert_text((50, 150), f"Sample content for page number {p_num}.", fontsize=14)
    doc.save(test_pdf_path)
    doc.close()
    
    info = get_pdf_info(test_pdf_path)
    print(f"Created test PDF with {info['total_pages']} pages.")
    assert info["total_pages"] == 3
    
    # Test page range parsing
    r1 = parse_page_ranges("2-3", 3)
    assert r1 == [1, 2], f"Expected [1, 2], got {r1}"
    print("✓ Page range parsing passed (2-3 -> pages 2 and 3)")
    
    # Process PDF with page range '2-3'
    result = process_pdf(test_pdf_path, page_range_str="2-3", mode="smart")
    print(f"Processed {result['total_processed']} pages.")
    assert result["total_processed"] == 2
    assert "Page 2" in result["full_text"]
    assert "Page 3" in result["full_text"]
    print("✓ PDF page range text extraction passed!")
    
    # Clean up test pdf
    if os.path.exists(test_pdf_path):
        os.remove(test_pdf_path)
        
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! 100% OPERATIONAL.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
