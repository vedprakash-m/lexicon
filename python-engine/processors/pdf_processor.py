import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image
import io
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class PDFExtractionResult:
    text: str
    metadata: Dict
    page_count: int
    extraction_method: str
    quality_score: float
    has_images: bool
    is_scanned: bool

class PDFProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def extract_text(self, pdf_path: str, password: Optional[str] = None) -> PDFExtractionResult:
        """Extract text from PDF using multiple engines with OCR fallback"""
        try:
            # Try PyMuPDF first
            result = self._extract_with_pymupdf(pdf_path, password)
            if result.quality_score > 0.7:
                return result
                
            # Try pdfplumber if PyMuPDF quality is low
            plumber_result = self._extract_with_pdfplumber(pdf_path, password)
            if plumber_result.quality_score > result.quality_score:
                result = plumber_result
                
            # Use OCR if text quality is still poor
            if result.quality_score < 0.5 or result.is_scanned:
                ocr_result = self._extract_with_ocr(pdf_path, password)
                if ocr_result.quality_score > result.quality_score:
                    result = ocr_result
                    
            return result
            
        except Exception as e:
            self.logger.error(f"PDF extraction failed: {e}")
            raise
            
    def _extract_with_pymupdf(self, pdf_path: str, password: Optional[str] = None) -> PDFExtractionResult:
        """Extract using PyMuPDF"""
        doc = fitz.open(pdf_path)
        if password:
            doc.authenticate(password)
            
        text_parts = []
        has_images = False
        total_chars = 0
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            page_text = page.get_text()
            text_parts.append(page_text)
            total_chars += len(page_text.strip())
            
            # Check for images
            if page.get_images():
                has_images = True
                
        full_text = "\n".join(text_parts)
        
        # Calculate quality score based on text density
        quality_score = min(1.0, total_chars / (doc.page_count * 100))
        is_scanned = quality_score < 0.1
        
        metadata = {
            'title': doc.metadata.get('title', ''),
            'author': doc.metadata.get('author', ''),
            'subject': doc.metadata.get('subject', ''),
            'creator': doc.metadata.get('creator', ''),
            'producer': doc.metadata.get('producer', ''),
            'creation_date': doc.metadata.get('creationDate', ''),
            'modification_date': doc.metadata.get('modDate', ''),
        }
        
        doc.close()
        
        return PDFExtractionResult(
            text=full_text,
            metadata=metadata,
            page_count=doc.page_count,
            extraction_method='pymupdf',
            quality_score=quality_score,
            has_images=has_images,
            is_scanned=is_scanned
        )
        
    def _extract_with_pdfplumber(self, pdf_path: str, password: Optional[str] = None) -> PDFExtractionResult:
        """Extract using pdfplumber"""
        with pdfplumber.open(pdf_path, password=password) as pdf:
            text_parts = []
            total_chars = 0
            
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
                total_chars += len(page_text.strip())
                
            full_text = "\n".join(text_parts)
            
            # Calculate quality score
            quality_score = min(1.0, total_chars / (len(pdf.pages) * 100))
            is_scanned = quality_score < 0.1
            
            metadata = pdf.metadata or {}
            
            return PDFExtractionResult(
                text=full_text,
                metadata=metadata,
                page_count=len(pdf.pages),
                extraction_method='pdfplumber',
                quality_score=quality_score,
                has_images=False,  # pdfplumber doesn't easily detect images
                is_scanned=is_scanned
            )
            
    def _extract_with_ocr(self, pdf_path: str, password: Optional[str] = None) -> PDFExtractionResult:
        """Extract using OCR as fallback"""
        doc = fitz.open(pdf_path)
        if password:
            doc.authenticate(password)
            
        text_parts = []
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            
            # Convert page to image
            mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # OCR the image
            image = Image.open(io.BytesIO(img_data))
            page_text = pytesseract.image_to_string(image)
            text_parts.append(page_text)
            
        full_text = "\n".join(text_parts)
        
        metadata = doc.metadata or {}
        doc.close()
        
        return PDFExtractionResult(
            text=full_text,
            metadata=metadata,
            page_count=doc.page_count,
            extraction_method='ocr',
            quality_score=0.8,  # OCR generally produces readable text
            has_images=True,
            is_scanned=True
        )
        
    def assess_quality(self, result: PDFExtractionResult) -> Dict:
        """Assess the quality of extracted text"""
        text = result.text
        
        # Basic quality metrics
        word_count = len(text.split())
        char_count = len(text)
        line_count = len(text.split('\n'))
        
        # Calculate readability metrics
        avg_word_length = sum(len(word) for word in text.split()) / max(word_count, 1)
        avg_line_length = char_count / max(line_count, 1)
        
        # Detect potential issues
        has_garbled_text = sum(1 for char in text if ord(char) > 127) / max(char_count, 1) > 0.1
        has_repeated_chars = any(char * 5 in text for char in 'abcdefghijklmnopqrstuvwxyz')
        
        return {
            'word_count': word_count,
            'char_count': char_count,
            'line_count': line_count,
            'avg_word_length': avg_word_length,
            'avg_line_length': avg_line_length,
            'quality_score': result.quality_score,
            'extraction_method': result.extraction_method,
            'has_garbled_text': has_garbled_text,
            'has_repeated_chars': has_repeated_chars,
            'is_scanned': result.is_scanned,
            'has_images': result.has_images
        }