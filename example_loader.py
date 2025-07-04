"""
Loads training examples (papers + their corresponding .seirmodel files) for few-shot learning
"""
import os
from pdf_processor import PDFProcessor

class ExampleLoader:
    """Loads and manages training examples for prompt generation"""
    
    def __init__(self, examples_dir: str = "reference_examples"):
        self.examples_dir = examples_dir
        self.pdf_processor = PDFProcessor()
        self.examples = self._load_examples()
    
    def _load_examples(self) -> list:
        """Load all paper-model pairs from examples directory"""
        examples = []
        
        if not os.path.exists(self.examples_dir):
            print(f"⚠️  Examples directory not found: {self.examples_dir}")
            return examples
        
        # Define known paper-model pairs
        example_pairs = [
            {
                "name": "COVID-19",
                "pdf_file": "covid.pdf",
                "seirmodel_file": "covid.seirmodel"
            },
            {
                "name": "HIV",
                "pdf_file": "Mathematical_Model_of_HIV.pdf", 
                "seirmodel_file": "HIV.seirmodel"
            }
        ]
        
        for pair in example_pairs:
            pdf_path = os.path.join(self.examples_dir, pair["pdf_file"])
            model_path = os.path.join(self.examples_dir, pair["seirmodel_file"])
            
            if os.path.exists(pdf_path) and os.path.exists(model_path):
                try:
                    # Extract text from PDF
                    paper_text = self.pdf_processor.extract_text(pdf_path)
                    clean_text = self.pdf_processor.clean_text(paper_text)
                    
                    # Read SEIR model
                    with open(model_path, 'r', encoding='utf-8') as f:
                        seir_model = f.read().strip()
                    
                    examples.append({
                        "name": pair["name"],
                        "paper_text": clean_text[:5000],  # Truncate for prompt size
                        "seir_model": seir_model
                    })
                    
                    print(f"✅ Loaded example: {pair['name']}")
                    
                except Exception as e:
                    print(f"❌ Failed to load {pair['name']}: {e}")
            else:
                print(f"⚠️  Missing files for {pair['name']}")
        
        return examples
    
    def get_examples_for_prompt(self) -> str:
        """Generate examples section for inclusion in prompts"""
        if not self.examples:
            return ""
        
        examples_text = """
## TRAINING EXAMPLES

Here are examples of how research papers have been successfully converted to SEIR models:

"""
        
        for i, example in enumerate(self.examples, 1):
            examples_text += f"""
### EXAMPLE {i}: {example['name']} Model

**Research Paper Extract:**
{example['paper_text'][:2000]}...

**Generated SEIR Model:**
```xml
{example['seir_model']}
```

---
"""
        
        examples_text += """
## INSTRUCTIONS

Using the above examples as guidance, analyze the provided research paper and generate a SEIR model following the same patterns and structure.

"""
        
        return examples_text
    
    def get_example_count(self) -> int:
        """Get number of loaded examples"""
        return len(self.examples)