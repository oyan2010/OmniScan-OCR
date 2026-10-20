"""
PDF processing module for OmniScan OCR.
Handles fast digital text extraction and scanned page OCR using PyMuPDF and OCR Engine.
Supports custom page ranges (e.g. 1-5, 3, 7-10).
"""
import os
import pymupdf  # PyMuPDF
from PIL import Image
from ocr_engine import recognize_text

def parse_page_ranges(range_str, total_pages):
    """
    Parse a page range string (1-indexed) into a list of 0-indexed page numbers.
    Examples:
        'all' -> [0, 1, 2, ..., total_pages - 1]
        '1-5' -> [0, 1, 2, 3, 4]
        '1, 3, 5-7' -> [0, 2, 4, 5, 6]
        '4' -> [3]
    """
    range_str = range_str.strip().lower()
    if not range_str or range_str == "all":
        return list(range(total_pages))
    
    selected_pages = set()
    parts = range_str.split(",")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            sub = part.split("-")
            try:
                start = int(sub[0].strip()) - 1
                end = int(sub[1].strip()) - 1
                start = max(0, min(start, total_pages - 1))
                end = max(0, min(end, total_pages - 1))
                if start <= end:
                    for p in range(start, end + 1):
                        selected_pages.add(p)
                else:
                    for p in range(end, start + 1):
                        selected_pages.add(p)
            except ValueError:
                pass
        else:
            try:
                p = int(part) - 1
                if 0 <= p < total_pages:
                    selected_pages.add(p)
            except ValueError:
                pass
                
    return sorted(list(selected_pages))

def get_pdf_info(pdf_path):
    """Return basic info about the PDF (total pages, metadata)."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    metadata = doc.metadata or {}
    doc.close()
    return {
        "total_pages": total_pages,
        "title": metadata.get("title", ""),
        "author": metadata.get("author", ""),
    }

def process_pdf(pdf_path, 
                page_range_str="all", 
                mode="smart", 
                engine="local", 
                lang_key="ur_en", 
                api_key="", 
                dpi=200, 
                progress_callback=None):
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to PDF.
        page_range_str: 'all' or '1-5, 8'.
        mode: 'smart' (use digital text if present, OCR if scanned) or 'force_ocr'.
        engine: 'local' (EasyOCR) or 'cloud' (Gemini).
        lang_key: Language key for OCR.
        api_key: Gemini API key if cloud engine.
        dpi: DPI resolution for rendering scanned pages (default 200).
        progress_callback: Callable(current_idx, total_count, page_num, text).
        
    Returns:
        dict: {
            'full_text': str,
            'pages': [{'page_num': int, 'text': str, 'source': 'digital'|'ocr'}],
            'total_processed': int
        }
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    page_indices = parse_page_ranges(page_range_str, total_pages)
    
    results = []
    total_to_process = len(page_indices)
    
    for idx, page_idx in enumerate(page_indices):
        page_num = page_idx + 1  # 1-indexed for human display
        page = doc[page_idx]
        
        extracted_text = ""
        source = "digital"
        
        if mode == "smart":
            # Check if digital text exists
            text = page.get_text()
            if text and len(text.strip()) > 25:
                extracted_text = text.strip()
                source = "digital"
            else:
                # Scanned image page: render and OCR
                source = "ocr"
        else:
            source = "ocr"
            
        if source == "ocr":
            # Render page to image
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            def sub_progress(msg):
                if progress_callback:
                    progress_callback(idx, total_to_process, page_num, f"Page {page_num}: {msg}")
                    
            extracted_text = recognize_text(
                img,
                engine=engine,
                lang_key=lang_key,
                api_key=api_key,
                progress_callback=sub_progress
            )
            
        page_result = {
            "page_num": page_num,
            "text": extracted_text,
            "source": source
        }
        results.append(page_result)
        
        if progress_callback:
            progress_callback(idx + 1, total_to_process, page_num, extracted_text)
            
    doc.close()
    
    full_text_blocks = []
    for p in results:
        full_text_blocks.append(f"--- [Page {p['page_num']} ({p['source'].upper()})] ---\n\n{p['text']}")
        
    return {
        "full_text": "\n\n".join(full_text_blocks),
        "pages": results,
        "total_processed": len(results)
    }
