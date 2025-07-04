"""
SEIR Model Generator - Converts PDF papers to .seirmodel files
"""
import os
import time
from datetime import datetime
from typing import Optional, Tuple
import google.generativeai as genai
from dotenv import load_dotenv

from pdf_processor import PDFProcessor
from seir_prompt import SEIRPromptGenerator

class SEIRModelGenerator:
    """Main class for generating SEIR models from PDF research papers"""
    
    def __init__(self, api_key: str = None):
        # Setup API key
        if api_key:
            genai.configure(api_key=api_key)
        else:
            try:
                env_path = os.path.join(os.path.dirname(__file__), ".env")
                load_dotenv(env_path)
                genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
            except KeyError:
                raise ValueError("GOOGLE_API_KEY environment variable not set. Please create .env file with your API key.")
        
        # Initialize components
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        self.pdf_processor = PDFProcessor()
        self.prompt_generator = SEIRPromptGenerator()
        
        # Create output directory
        self.output_dir = "generated_models"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_from_pdf(self, pdf_path: str, output_name: str = None) -> Tuple[bool, str, str]:
        """
        Generate SEIR model from PDF paper
        
        Args:
            pdf_path: Path to PDF file
            output_name: Name for output files (auto-generated if None)
            
        Returns:
            Tuple of (success, seir_model_xml, output_file_path)
        """
        print(f"🔄 Processing PDF: {pdf_path}")
        
        # Generate output name if not provided
        if output_name is None:
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"{base_name}_{timestamp}"
        
        try:
            # Step 1: Extract text from PDF
            print("📄 Extracting text from PDF...")
            paper_text = self.pdf_processor.extract_text(pdf_path)
            clean_text = self.pdf_processor.clean_text(paper_text)
            
            if len(clean_text.strip()) < 100:
                return False, "", f"Error: Extracted text too short ({len(clean_text)} characters)"
            
            print(f"✅ Extracted {len(clean_text)} characters from PDF")
            
            # Step 2: Generate SEIR model
            print("🧠 Generating SEIR model...")
            prompt = self.prompt_generator.generate_extraction_prompt(clean_text)
            
            response = self.model.generate_content(prompt)
            raw_gemini_response = response.text.strip()
            
            # Step 3: Clean XML response
            seir_xml = self._clean_xml_response(raw_gemini_response)
            
            # Step 4: Validate and potentially improve
            print("✅ Validating generated model...")
            seir_xml = self._validate_and_improve(seir_xml)
            
            # Step 5: Save files
            output_files = self._save_results(seir_xml, output_name)
            
            print(f"✅ Successfully generated SEIR model: {output_files['seirmodel']}")
            return True, seir_xml, output_files['seirmodel']
            
        except Exception as e:
            error_msg = f"Error generating SEIR model: {str(e)}"
            print(f"❌ {error_msg}")
            return False, "", error_msg
    
    def _clean_xml_response(self, response: str) -> str:
        """Extract clean XML from model response"""
        # Find XML content markers
        start_markers = ["<?xml", "<seir:SEIRModel"]
        end_marker = "</seir:SEIRModel>"
        
        # Find start
        start_idx = -1
        for marker in start_markers:
            idx = response.find(marker)
            if idx != -1:
                start_idx = idx
                break
        
        # Find end
        end_idx = response.rfind(end_marker)
        if end_idx != -1:
            end_idx += len(end_marker)
        
        # Extract XML content
        if start_idx != -1 and end_idx != -1:
            xml_content = response[start_idx:end_idx]
        elif start_idx != -1:
            xml_content = response[start_idx:]
        else:
            xml_content = response
        
        # Ensure proper XML declaration
        if not xml_content.strip().startswith("<?xml"):
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_content.strip()
        
        return xml_content.strip()
    
    def _validate_and_improve(self, seir_xml: str) -> str:
        """Validate generated XML and improve if needed"""
        try:
            # Basic XML validation
            import xml.etree.ElementTree as ET
            ET.fromstring(seir_xml)
            
            # Check for common issues and auto-fix
            seir_xml = self._auto_fix_common_issues(seir_xml)
            
            return seir_xml
            
        except ET.ParseError as e:
            print(f"⚠️  XML validation failed: {e}")
            print("🔄 Attempting to fix XML issues...")
            
            # Try to get improved version from model
            validation_prompt = self.prompt_generator.generate_validation_prompt(seir_xml)
            try:
                response = self.model.generate_content(validation_prompt)
                improved_xml = self._clean_xml_response(response.text)
                
                # Test if improved version is valid
                ET.fromstring(improved_xml)
                print("✅ XML issues fixed")
                return improved_xml
                
            except:
                print("❌ Could not fix XML issues, returning original")
                return seir_xml
    
    def _auto_fix_common_issues(self, xml_content: str) -> str:
        """Fix common XML formatting issues"""
        import re
        
        # Fix namespace issues
        if 'xmlns:seir="http://example.com/seirmodel"' not in xml_content:
            xml_content = xml_content.replace(
                '<seir:SEIRModel',
                '<seir:SEIRModel xmi:version="2.0" xmlns:xmi="http://www.omg.org/XMI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:seir="http://example.com/seirmodel"'
            )
        
        # Fix self-closing tags for compartments without flows
        xml_content = re.sub(
            r'<compartments([^>]*)>\s*</compartments>',
            r'<compartments\1/>',
            xml_content
        )
        
        # Ensure proper numeric rates (remove any remaining expressions)
        rate_pattern = r'rate="([^"]*[+\-*/()][^"]*)"'
        def fix_rate(match):
            rate_expr = match.group(1)
            try:
                # Try to evaluate simple expressions
                result = eval(rate_expr.replace('*', '*').replace('/', '/'))
                return f'rate="{result}"'
            except:
                return f'rate="0.1"'  # Default fallback
        
        xml_content = re.sub(rate_pattern, fix_rate, xml_content)
        
        return xml_content
    
    def _save_results(self, seir_xml: str, output_name: str) -> dict:
        """Save only the .seirmodel file"""
        
        output_files = {}
        
        # Save SEIR model
        seir_path = os.path.join(self.output_dir, f"{output_name}.seirmodel")
        with open(seir_path, 'w', encoding='utf-8') as f:
            f.write(seir_xml)
        output_files['seirmodel'] = seir_path
        
        return output_files
    
    def batch_process(self, pdf_files: list, delay_seconds: int = 5) -> list:
        """Process multiple PDF files in batch"""
        results = []
        
        for i, pdf_path in enumerate(pdf_files):
            print(f"\n🔄 Processing {i+1}/{len(pdf_files)}: {pdf_path}")
            
            success, seir_xml, output_path = self.generate_from_pdf(pdf_path)
            
            results.append({
                'pdf_path': pdf_path,
                'success': success,
                'output_path': output_path,
                'seir_xml': seir_xml if success else None
            })
            
            # Add delay between requests to avoid rate limiting
            if i < len(pdf_files) - 1:
                print(f"⏳ Waiting {delay_seconds} seconds...")
                time.sleep(delay_seconds)
        
        return results