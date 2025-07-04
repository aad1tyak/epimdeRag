"""
Main script for PDF to SEIR model conversion
"""
import os
import sys
from seir_generator import SEIRModelGenerator

def print_separator():
    """Print visual separator"""
    print("=" * 80)

def print_result(success: bool, output_path: str, pdf_name: str):
    """Print generation result"""
    if success:
        print(f"✅ SUCCESS: {pdf_name}")
        print(f"📁 Generated: {output_path}")
    else:
        print(f"❌ FAILED: {pdf_name}")
        print(f"🔴 Error: {output_path}")
    print()

def process_single_pdf(generator: SEIRModelGenerator, pdf_path: str):
    """Process a single PDF file"""
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print(f"🔄 Processing: {os.path.basename(pdf_path)}")
    success, seir_xml, output_path = generator.generate_from_pdf(pdf_path)
    print_result(success, output_path, os.path.basename(pdf_path))
    
    return success

def ask_for_pdf_input(generator: SEIRModelGenerator):
    """Ask user for PDF filename and process it"""
    papers_dir = "new_papers"
    
    # Create directory if it doesn't exist
    if not os.path.exists(papers_dir):
        os.makedirs(papers_dir)
        print(f"📁 Created directory: {papers_dir}")
        print(f"📄 Please place your PDF files in the '{papers_dir}' folder")
        return
    
    # List available PDF files
    pdf_files = [f for f in os.listdir(papers_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"❌ No PDF files found in {papers_dir}")
        print(f"📄 Please place your PDF files in the '{papers_dir}' folder")
        return
    
    print(f"📚 Available PDF files in {papers_dir}:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf_file}")
    
    print_separator()
    
    # Ask for input
    while True:
        pdf_name = input("📄 Enter the PDF filename (with .pdf extension): ").strip()
        
        if not pdf_name:
            print("❌ Please enter a filename")
            continue
        
        # Add .pdf extension if not provided
        if not pdf_name.lower().endswith('.pdf'):
            pdf_name += '.pdf'
        
        pdf_path = os.path.join(papers_dir, pdf_name)
        
        if os.path.exists(pdf_path):
            print(f"✅ Found: {pdf_name}")
            success = process_single_pdf(generator, pdf_path)
            if success:
                print(f"📁 Generated model saved in: generated_models/")
            break
        else:
            print(f"❌ File not found: {pdf_name}")
            print("Available files:")
            for pdf_file in pdf_files:
                print(f"  - {pdf_file}")
            
            retry = input("🔄 Try again? (y/n): ").strip().lower()
            if retry != 'y':
                break


def main():
    """Main function"""
    print("🔬 PDF to SEIR Model Converter")
    print("Converts epidemiological research papers to .seirmodel files")
    print_separator()
    
    try:
        # Initialize generator
        print("🚀 Initializing SEIR Model Generator...")
        generator = SEIRModelGenerator()
        print("✅ Generator initialized successfully")
        print_separator()
        
        # Ask for PDF input
        ask_for_pdf_input(generator)
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("💡 Make sure you have created a .env file with your GOOGLE_API_KEY")
        return
    
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return

if __name__ == "__main__":
    main()