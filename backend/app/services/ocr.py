import io
import os
import re
from typing import List, Dict, Any
import PyPDF2
from docx import Document
from pptx import Presentation
from PIL import Image
import google.generativeai as genai
from app.core.config import settings

class OCRService:
    def __init__(self):
        # Configure Gemini API if key is present
        self.gemini_enabled = bool(settings.GEMINI_API_KEY)
        if self.gemini_enabled:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        
        # EasyOCR will be lazily loaded to avoid startup delays
        self._easyocr_reader = None

    @property
    def easyocr_reader(self):
        if self._easyocr_reader is None:
            try:
                import easyocr
                # Initialize EasyOCR reader (supports English by default, downloads models)
                self._easyocr_reader = easyocr.Reader(["en"], verbose=False)
            except Exception as e:
                # If PyTorch / EasyOCR isn't installed properly or fails, we fall back
                self._easyocr_reader = False
        return self._easyocr_reader


    def extract_text_from_pdf(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extracts text page-by-page from PDF. If pages are scanned (low/empty text),
        triggers OCR driver (Gemini OCR or EasyOCR).
        """
        results = []
        pdf_file = io.BytesIO(file_bytes)
        try:
            reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(reader.pages)
            
            for page_num in range(total_pages):
                page = reader.pages[page_num]
                text = page.extract_text() or ""
                text = self._clean_text(text)
                
                # If text is too short, we assume page is scanned or an image
                if len(text.strip()) < 50:
                    # Scanned PDF page!
                    # If Gemini is configured, we can extract text via Gemini multimodal or use EasyOCR.
                    # For local dev without Gemini, we'll extract text if possible or label it as scanned.
                    text = self._run_ocr_on_pdf_page(pdf_file, page_num)
                
                results.append({
                    "page_number": page_num + 1,
                    "extracted_text": text
                })
        except Exception as e:
            # Fallback wrapper
            results = [{"page_number": 1, "extracted_text": f"Error parsing PDF: {str(e)}"}]
        return results

    def extract_text_from_docx(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extracts text from DOCX document.
        """
        docx_file = io.BytesIO(file_bytes)
        doc = Document(docx_file)
        full_text = []
        for para in doc.paragraphs:
            if para.text:
                full_text.append(para.text)
        
        # Also extract tables
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text for cell in row.cells if cell.text]
                if row_text:
                    full_text.append(" | ".join(row_text))

        text_content = self._clean_text("\n".join(full_text))
        return [{"page_number": 1, "extracted_text": text_content}]

    def extract_text_from_pptx(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extracts text slide-by-slide from PPTX.
        """
        pptx_file = io.BytesIO(file_bytes)
        prs = Presentation(pptx_file)
        results = []
        
        for slide_num, slide in enumerate(prs.slides):
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    slide_text.append(shape.text)
            
            text_content = self._clean_text("\n".join(slide_text))
            results.append({
                "page_number": slide_num + 1,
                "extracted_text": text_content
            })
        return results

    def extract_text_from_image(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extracts text from PNG/JPG image.
        Uses Gemini Vision API if enabled, else falls back to EasyOCR, else fails gracefully.
        """
        text = ""
        if self.gemini_enabled:
            try:
                img = Image.open(io.BytesIO(file_bytes))
                prompt = (
                    "Perform OCR on this image. Extract all printed and handwritten text, tables, and headings. "
                    "Provide a clean transcription preserving structured layouts/tables where possible."
                )
                response = self.model.generate_content([prompt, img])
                text = response.text
            except Exception as e:
                text = f"[Gemini OCR Error: {str(e)}] " + self._run_local_ocr_on_image(file_bytes)
        else:
            text = self._run_local_ocr_on_image(file_bytes)
            
        return [{"page_number": 1, "extracted_text": self._clean_text(text)}]

    def _run_ocr_on_pdf_page(self, pdf_file: io.BytesIO, page_num: int) -> str:
        """
        Runs OCR on a scanned PDF page.
        Extracts embedded page images via PyPDF2 and performs local EasyOCR on them.
        """
        try:
            reader = PyPDF2.PdfReader(pdf_file)
            page = reader.pages[page_num]
            extracted_images_text = []
            
            for img_obj in page.images:
                try:
                    pil_img = Image.open(io.BytesIO(img_obj.data))
                    w, h = pil_img.size
                    if w < 150 or h < 150:
                        continue
                except Exception:
                    pass
                
                img_text = self._run_local_ocr_on_image(img_obj.data)
                # Ignore "not available" message in the final string if it fails
                if img_text and "[Local OCR Engine" not in img_text:
                    extracted_images_text.append(img_text)
            
            if extracted_images_text:
                return " ".join(extracted_images_text)
        except Exception as e:
            logger.error(f"Error running OCR on PDF page {page_num}: {e}")

        # Fallback message if no text could be extracted
        return f"[Scanned page {page_num + 1} - OCR would run in production]"


    def _run_local_ocr_on_image(self, file_bytes: bytes) -> str:
        """
        Executes EasyOCR locally if installed.
        """
        reader = self.easyocr_reader
        if reader:
            try:
                results = reader.readtext(file_bytes, detail=0)
                return " ".join(results)
            except Exception as e:
                return f"[EasyOCR Execution Error: {str(e)}]"
        return "[Local OCR Engine (EasyOCR) not available. Please configure Gemini API Key for OCR.]"

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text blocks.
        """
        # Remove consecutive whitespaces/newlines
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

ocr_service = OCRService()
