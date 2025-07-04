# EpimdeRag: Automated SEIR Model Generation from Research Papers

An intelligent system that automatically converts epidemiological research papers (PDF format) into SEIR model files (.seirmodel) using AI-powered few-shot learning. The system leverages existing successful extractions to achieve high accuracy and consistency with the Model-Driven-Epidemiology framework.

## 🎯 Overview

EpimdeRag addresses the challenge of manually creating epidemiological models from research literature. By using AI with domain-specific training examples, it automates the extraction of SEIR (Susceptible-Exposed-Infectious-Recovered) models while maintaining compatibility with existing modeling frameworks.

### Key Features

- **📄 PDF-to-Model Conversion**: Direct conversion from research papers to .seirmodel files
- **🧠 Few-Shot Learning**: Uses existing successful extractions as training examples
- **🔍 Intelligent Processing**: Robust PDF text extraction with automatic cleaning
- **✅ Quality Assurance**: Built-in validation and error correction
- **🎯 Clean Output**: Generates only the essential .seirmodel file
- **⚡ Fast Processing**: Automated pipeline from paper to model in minutes

## 🏗️ Architecture

```
epimdeRag/
├── 📁 reference_examples/          # Training examples for few-shot learning
│   ├── covid.pdf                   # COVID-19 research paper
│   ├── covid.seirmodel             # Corresponding SEIR model
│   ├── Mathematical_Model_of_HIV.pdf # HIV research paper
│   └── HIV.seirmodel               # Corresponding SEIR model
├── 📁 new_papers/                  # Input folder for new PDFs to process
├── 📁 generated_models/            # Output folder for generated .seirmodel files
├── 🔧 seir_generator.py            # Core PDF→SEIR conversion engine
├── 🧠 seir_prompt.py               # AI prompt generation with examples
├── 📄 pdf_processor.py             # Robust PDF text extraction
├── 📚 example_loader.py            # Few-shot learning example management
├── 🎛️ main.py                      # Main execution interface
└── 📦 requirements.txt             # Dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- Google AI API key (Gemini)

### Installation

1. **Clone and navigate to the project:**
```bash
cd epimdeRag
```

2. **Set up virtual environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies:**
```bash
.venv/bin/pip install -r requirements.txt
```

4. **Configure API key:**
Create a `.env` file in the project root:
```bash
echo "GOOGLE_API_KEY=your_google_api_key_here" > .env
```

### Basic Usage

1. **Add your PDF paper** to the `new_papers/` folder:
```bash
cp your_paper.pdf new_papers/
```

2. **Run the conversion:**
```bash
.venv/bin/python3 test_single.py
```

3. **Find your generated model** in `generated_models/`:
```bash
ls generated_models/
# Output: your_paper_20231203_143052.seirmodel
```

## 🔬 How It Works

### 1. Few-Shot Learning Approach

The system uses proven successful extractions as training examples:

```
Training Examples:
├── COVID-19 Paper → covid.seirmodel
└── HIV Paper → HIV.seirmodel

New Paper Input → AI Analysis → Generated .seirmodel
```

### 2. Processing Pipeline

```mermaid
graph LR
    A[PDF Paper] --> B[Text Extraction]
    B --> C[Prompt Generation]
    C --> D[AI Analysis]
    D --> E[XML Generation]
    E --> F[Validation]
    F --> G[.seirmodel File]
```

**Detailed Steps:**
1. **PDF Processing**: Extract and clean text using multiple extraction methods
2. **Example Loading**: Load training examples (COVID & HIV papers + models)
3. **Prompt Engineering**: Create comprehensive prompt with examples and guidelines
4. **AI Generation**: Send to Gemini AI for model extraction
5. **Validation**: Automatic XML validation and error correction
6. **Output**: Clean .seirmodel file ready for use

### 3. Example Integration

The AI receives prompts like:
```
## TRAINING EXAMPLES

### EXAMPLE 1: COVID-19 Model
**Research Paper Extract:**
[COVID paper content...]

**Generated SEIR Model:**
```xml
<seir:SEIRModel>
  <compartments PrimaryName="Susceptible">
    <outgoingFlows rate="0.0276" target="//@compartments.1"/>
  </compartments>
  <!-- ... complete model ... -->
</seir:SEIRModel>
```

### EXAMPLE 2: HIV Model
[Similar structure for HIV...]

## NEW RESEARCH PAPER TO ANALYZE:
[Your paper content...]
```

## 📊 Output Format

Generated `.seirmodel` files follow the exact format required by Model-Driven-Epidemiology:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<seir:SEIRModel xmi:version="2.0" 
                xmlns:xmi="http://www.omg.org/XMI" 
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                xmlns:seir="http://example.com/seirmodel">
  
  <compartments PrimaryName="Susceptible">
    <outgoingFlows rate="0.21" target="//@compartments.1" 
                   description="infection"/>
  </compartments>
  
  <compartments PrimaryName="Exposed">
    <outgoingFlows rate="0.143" target="//@compartments.2" 
                   description="progression to infectious"/>
  </compartments>
  
  <!-- Additional compartments... -->
  
</seir:SEIRModel>
```

**Key Features:**
- ✅ **Standard XML structure** with required namespaces
- ✅ **Numeric rate values** (calculated, not expressions)
- ✅ **Proper indexing** (0-based compartment references)
- ✅ **Epidemiological accuracy** following established patterns

## 🛠️ Advanced Usage

### Processing Multiple Papers

To process multiple papers, add them to `new_papers/` and modify `test_single.py`:

```python
# Process all PDFs in new_papers folder
papers = ["paper1.pdf", "paper2.pdf", "paper3.pdf"]
for paper in papers:
    success, xml, output = generator.generate_from_pdf(f"new_papers/{paper}")
    if success:
        print(f"✅ {paper} → {output}")
```

### Custom Processing

```python
from seir_generator import SEIRModelGenerator

generator = SEIRModelGenerator()
success, seir_xml, output_path = generator.generate_from_pdf("new_papers/my_paper.pdf")

if success:
    print(f"Generated: {output_path}")
    print(f"XML content: {seir_xml[:200]}...")
else:
    print(f"Error: {output_path}")
```
## 🧪 Testing

### Test with Sample Paper

The system includes a test script for quick validation:

```bash
.venv/bin/python3 test_single.py
```

This will process the sample paper in `new_papers/` and generate output in `generated_models/`.

### Validation Tests

To verify the system is working correctly:

1. **Check training examples loaded:**
```bash
.venv/bin/python3 -c "from example_loader import ExampleLoader; el = ExampleLoader(); print(f'Loaded {el.get_example_count()} examples')"
```

2. **Test PDF processing:**
```bash
.venv/bin/python3 -c "from pdf_processor import PDFProcessor; pp = PDFProcessor(); text = pp.extract_text('reference_examples/covid.pdf'); print(f'Extracted {len(text)} characters')"
```

## 🔧 Troubleshooting

### Common Issues

**1. API Key Error**
```
Error: GOOGLE_API_KEY environment variable not set
```
**Solution:** Create `.env` file with your API key.

**2. PDF Extraction Failed**
```
Error: Extracted text too short
```
**Solution:** Check if PDF is text-based (not scanned images) or try a different PDF.

**3. Module Not Found**
```
ModuleNotFoundError: No module named 'PyPDF2'
```
**Solution:** Install dependencies: `.venv/bin/pip install -r requirements.txt`

**4. Empty Generated Models**
```
Generated model is empty or invalid
```
**Solution:** Check if the paper contains sufficient epidemiological content.

### Debug Mode

Add debug prints to see processing steps:

```python
# In seir_generator.py, add:
print(f"Extracted text: {clean_text[:500]}...")
print(f"Generated XML: {seir_xml[:500]}...")
```

### Log Files

The system outputs processing information to console. For persistent logging:

```bash
.venv/bin/python3 test_single.py > processing.log 2>&1
```
