"""
PDF Processing module for extracting text from research papers
"""
import PyPDF2
import pdfplumber

class PDFProcessor:
    """Extracts text content from PDF files"""
    
    def __init__(self):
        pass
    
    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2 (faster but less accurate)"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            raise ValueError(f"Error extracting text with PyPDF2: {e}")
    
    def extract_text_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber (more accurate but slower)"""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error extracting text with pdfplumber: {e}")
    
    def extract_text(self, pdf_path: str, use_pdfplumber: bool = True) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            use_pdfplumber: If True, use pdfplumber (more accurate), else use PyPDF2 (faster)
        
        Returns:
            Extracted text content
        """
        if use_pdfplumber:
            try:
                return self.extract_text_pdfplumber(pdf_path)
            except:
                # Fallback to PyPDF2 if pdfplumber fails
                return self.extract_text_pypdf2(pdf_path)
        else:
            return self.extract_text_pypdf2(pdf_path)
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text by removing excessive whitespace and formatting issues"""
        import re
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove page headers/footers (common patterns)
        text = re.sub(r'\n\d+\n', '\n', text)  # Remove standalone page numbers
        text = re.sub(r'\n[A-Z\s]+\n', '\n', text)  # Remove ALL CAPS headers
        
        # Clean up common PDF artifacts
        text = text.replace('•', '-')  # Replace bullets
        text = text.replace("'", "'")  # Replace smart quotes
        text = text.replace('"', '"').replace('"', '"')  # Replace smart quotes
        
        return text.strip()