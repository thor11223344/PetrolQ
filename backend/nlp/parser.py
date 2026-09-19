import os
from typing import Any
import pymupdf as fitz
import pdfplumber
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DrillingReportParser:
    def __init__(self):
        pass

    def extract_text_and_tables(self, pdf_path: str) -> tuple[str, bool]:
        """
        Extracts narrative text using PyMuPDF and tables using pdfplumber.
        Combines them into a single string formatted for LLM consumption.
        """
        if not os.path.exists(pdf_path):
            logger.error(f"File not found: {pdf_path}")
            return "", False

        extracted_content = []

        ocr_triggered = False
        try:
            # 1. Extract tables using pdfplumber and convert to Markdown
            table_content_by_page = {}
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    if tables:
                        page_tables_md = []
                        for table in tables:
                            md_table = self._format_table_to_markdown(table)
                            if md_table:
                                page_tables_md.append(md_table)
                        if page_tables_md:
                            table_content_by_page[page_num] = "\n\n".join(page_tables_md)

            # 2. Extract text using PyMuPDF (fitz) with OCR fallback
            with fitz.open(pdf_path) as doc:
                if doc.needs_pass:
                    logger.error(f"PDF is encrypted/password-protected: {pdf_path}")
                    return "", False
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text("text")
                    
                    # Anti-Fabrication: If extracted text is under ~50 chars, rasterize page and run OCR fallback
                    if len(text.strip()) < 50:
                        try:
                            import easyocr
                            import numpy as np
                            from PIL import Image
                            import io
                            
                            if not hasattr(self, "ocr_reader"):
                                self.ocr_reader = easyocr.Reader(['en'], gpu=False)
                                
                            pix = page.get_pixmap(dpi=150)
                            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                            img_np = np.array(img)
                            
                            ocr_results = self.ocr_reader.readtext(img_np, detail=0)
                            ocr_result = "\n".join(ocr_results)
                            
                            if ocr_result and len(ocr_result.strip()) > 10:
                                text = f"[OCR Fallback Active - Scanned Page]:\n{ocr_result.strip()}"
                                ocr_triggered = True
                        except Exception as ocr_err:
                            logger.info(f"EasyOCR fallback attempt failed: {ocr_err}")
                    
                    if text.strip():
                        extracted_content.append(f"--- Page {page_num + 1} Text ---\n{text.strip()}")
                    
                    # Append any tables found on this page directly after the text
                    if page_num in table_content_by_page:
                        extracted_content.append(f"--- Page {page_num + 1} Tables ---\n{table_content_by_page[page_num]}")

            return "\n\n".join(extracted_content), ocr_triggered

        except Exception as e:
            logger.error(f"Failed to parse PDF {pdf_path}: {e}")
            return "", False

    def _format_table_to_markdown(self, table: list[list[Any]]) -> str:
        """
        Converts a 2D list table from pdfplumber into a Markdown table string.
        """
        if not table or len(table) < 2:
            return ""
        
        # Clean up None values and newlines within cells
        clean_table = []
        for row in table:
            clean_row = [str(cell).replace('\n', ' ').strip() if cell is not None else "" for cell in row]
            # Only add rows that aren't entirely empty
            if any(clean_row):
                clean_table.append(clean_row)
                
        if not clean_table or len(clean_table) < 2:
             return ""

        headers = clean_table[0]
        # Pad headers if rows have more columns
        max_cols = max(len(row) for row in clean_table)
        if len(headers) < max_cols:
            headers.extend([""] * (max_cols - len(headers)))

        md_rows = []
        # Header row
        md_rows.append("| " + " | ".join(headers) + " |")
        # Separator row
        md_rows.append("|" + "|".join(["---" for _ in headers]) + "|")
        
        # Data rows
        for row in clean_table[1:]:
            if len(row) < max_cols:
                row.extend([""] * (max_cols - len(row)))
            md_rows.append("| " + " | ".join(row) + " |")
            
        return "\n".join(md_rows)

    def create_operational_chunks(self, raw_text: str, max_chunk_size: int = 1500) -> list[str]:
        """
        Splits text logically by operational boundaries or token length,
        incorporating an overlap to preserve context between chunks.
        """
        if not raw_text.strip():
            return []
            
        try:
            # Utilize LangChain's RecursiveCharacterTextSplitter for robust logical boundary chunking
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=max_chunk_size,
                chunk_overlap=200,
                # Try splitting by our custom structural markers first, falling back to paragraphs/sentences
                separators=[
                    "\n\n--- Page", 
                    "\n\n24-Hour Summary", 
                    "\n\nIncidents / NPT", 
                    "\n\nRemarks", 
                    "\n\n", 
                    "\n", 
                    " ", 
                    ""
                ]
            )
            return splitter.split_text(raw_text)
        except Exception as e:
            logger.error(f"Failed to chunk text: {e}")
            return []
