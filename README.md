# PDF to SEIR Model Generator

A focused system that converts epidemiological research papers (PDF format) directly into .seirmodel files using AI-powered extraction and the metamodel derived from existing Model-Driven-Epidemiology examples.

## 🎯 Purpose

This system analyzes epidemiological research papers and automatically generates XML-based SEIR models that are compatible with your Model-Driven-Epidemiology framework.

## 📋 Features

- **PDF Text Extraction**: Robust PDF processing with multiple extraction methods
- **Intelligent Model Generation**: AI-powered analysis of epidemiological content  
- **Metamodel-Based Validation**: Uses patterns from existing HIV and COVID models
- **Clean Output**: Generates proper .seirmodel XML files
- **Batch Processing**: Handle multiple papers at once

## 🚀 Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Setup API Key
Create a `.env` file with your Google API key:
```
GOOGLE_API_KEY=your_google_api_key_here
```

### 3. Add Your Papers
Place PDF files in the `papers/` folder (you already have `Mathematical_Model_of_HIV.pdf` and `covid.pdf`)

### 4. Run the Generator
```bash
python main.py
```

This will process all PDFs in the papers folder and generate .seirmodel files in the `generated_models/` directory.

## 📁 Project Structure

```
epimdeRag/
├── main.py                    # Main execution script
├── seir_generator.py          # Core generation engine  
├── seir_prompt.py            # Prompt generation based on existing models
├── pdf_processor.py          # PDF text extraction
├── metamodel.json            # SEIR metamodel from existing examples
├── papers/                   # Input PDF files
│   ├── Mathematical_Model_of_HIV.pdf
│   └── covid.pdf
└── generated_models/         # Output .seirmodel files (created automatically)
```

## 🔍 How It Works

### 1. PDF Processing
- Extracts text using `pdfplumber` (primary) and `PyPDF2` (fallback)
- Cleans text by removing headers, page numbers, and formatting artifacts

### 2. Intelligent Prompting  
The system uses patterns learned from your existing model extractions:

**HIV Model Pattern** (from Mathematical_Model_of_HIV.pdf → HIV.seirmodel):
- Recruitment compartments by demographic groups
- Risk-stratified susceptible populations (MSM, women, heterosexual men)
- Treatment progression (Untreated → ART → AIDS)
- Multiple death states (AIDS death, natural death)

**COVID Model Pattern** (from covid.pdf → covid.seirmodel):
- Standard SEIR progression with severity stratification
- Isolation and quarantine states
- Hospital and ICU progression
- Single death and recovery states

### 3. XML Generation
- Converts extracted epidemiological information into proper XML format
- Ensures numeric rate values (not symbolic expressions)
- Validates compartment indexing and flow targets
- Follows the exact .seirmodel format from your existing models

## 📊 Output Files

For each processed PDF, the system generates:
- `{paper_name}.seirmodel` - The main SEIR model XML file
- `{paper_name}_extracted_text.txt` - Cleaned text from the PDF
- `{paper_name}_prompt.txt` - The AI prompt used
- `{paper_name}_metadata.json` - Generation metadata

## 🎛️ Usage Options

### Process All Papers
```bash
python main.py
```

### Process Specific PDF
```bash
python main.py path/to/your/paper.pdf
```

### Programmatic Usage
```python
from seir_generator import SEIRModelGenerator

generator = SEIRModelGenerator()
success, seir_xml, output_path = generator.generate_from_pdf("papers/covid.pdf")

if success:
    print(f"Generated model: {output_path}")
else:
    print(f"Error: {output_path}")
```

## 🔧 Customization

### Adding New Disease Patterns
Edit `seir_prompt.py` to add patterns for new disease types:

```python
self.extraction_patterns["measles_patterns"] = {
    "compartments": ["Susceptible", "Exposed", "Infectious", "Recovered"],
    "key_parameters": ["R0", "incubation_period", "infectious_period"],
    # ... additional patterns
}
```

### Adjusting Extraction Quality
In `pdf_processor.py`, choose between extraction methods:
- `use_pdfplumber=True` - More accurate, slower
- `use_pdfplumber=False` - Faster, less accurate

## ✅ Validation

The system includes automatic validation:
- **XML Structure**: Proper format and namespaces
- **Compartment Logic**: Realistic epidemiological flow
- **Rate Values**: Ensures numeric values, not expressions
- **Index References**: Validates compartment targeting

## 🔍 Example Output

Input: `Mathematical_Model_of_HIV.pdf`
Output: `Mathematical_Model_of_HIV.seirmodel`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<seir:SEIRModel xmi:version="2.0" xmlns:xmi="http://www.omg.org/XMI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:seir="http://example.com/seirmodel">
  <compartments PrimaryName="Recruitment" SecondaryName="Homosexual Men">
    <outgoingFlows rate="12.7872" target="//@compartments.3" description="Recruitment to susceptible"/>
  </compartments>
  <compartments PrimaryName="Susceptible" SecondaryName="Homosexual Men">
    <outgoingFlows rate="0.09636" target="//@compartments.6" description="Transmission"/>
    <outgoingFlows rate="0.0129" target="//@compartments.12" description="Natural death"/>
  </compartments>
  <!-- ... additional compartments ... -->
</seir:SEIRModel>
```

## 🐛 Troubleshooting

### Common Issues

1. **API Key Error**: Make sure `.env` file exists with valid `GOOGLE_API_KEY`
2. **PDF Extraction Failed**: Try different PDF or check file corruption
3. **Invalid XML Generated**: System will auto-fix common issues or retry generation
4. **Empty Output**: PDF might be image-based or have complex formatting

### Debug Mode
Add print statements in `seir_generator.py` to see intermediate steps:
```python
print(f"Extracted text length: {len(clean_text)}")
print(f"Generated XML length: {len(seir_xml)}")
```

## 📈 Performance Tips

- **Batch Processing**: Use for multiple papers with automatic rate limiting
- **PDF Quality**: Higher quality PDFs produce better text extraction
- **Paper Length**: Very long papers might need chunking for best results

## 🤝 Contributing

To add support for new model types:
1. Add extraction patterns to `seir_prompt.py`
2. Update metamodel.json with new compartment types
3. Test with representative papers
4. Submit improvements

## 📝 License

MIT License - Use freely for research and development.