#!/usr/bin/env python3
"""
Test script to process a single PDF
"""
from seir_generator import SEIRModelGenerator

def main():
    print("🔬 Testing PDF to SEIR Model Converter")
    print("="*50)
    
    try:
        # Initialize generator
        print("🚀 Initializing...")
        generator = SEIRModelGenerator()
        print("✅ Generator ready")
        
        # Test with new paper
        pdf_path = "new_papers/s41592-020-0856-2.pdf"
        print(f"📄 Processing: {pdf_path}")
        
        success, seir_xml, output_path = generator.generate_from_pdf(pdf_path)
        
        if success:
            print("✅ SUCCESS!")
            print(f"📁 Generated: {output_path}")
            print(f"📝 XML length: {len(seir_xml)} characters")
        else:
            print("❌ FAILED!")
            print(f"🔴 Error: {output_path}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()