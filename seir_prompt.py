"""
SEIR Model Prompt Generator based on analysis of existing paper-to-model extractions
"""
import json
from typing import Dict, Any
from example_loader import ExampleLoader

class SEIRPromptGenerator:
    """Generates prompts for converting research papers to SEIR models"""
    
    def __init__(self, metamodel_path: str = "metamodel.json"):
        self.metamodel = self._load_metamodel(metamodel_path)
        self.example_loader = ExampleLoader()
        print(f"📚 Loaded {self.example_loader.get_example_count()} training examples")
        
        # Analysis patterns from existing HIV and COVID extractions
        self.extraction_patterns = {
            "hiv_patterns": {
                "compartments": [
                    "Recruitment (by demographic group)",
                    "Susceptible (by risk group)", 
                    "Untreated Infected (by risk group)",
                    "Treated with ART",
                    "People living with AIDS", 
                    "Death due to AIDS",
                    "Natural Death"
                ],
                "demographic_stratification": ["Homosexual Men", "Women", "Heterosexual Men"],
                "key_parameters": ["Ψ", "θ", "γ", "p", "μ", "d", "δ", "α", "β", "c"],
                "flow_patterns": [
                    "Recruitment → Susceptible",
                    "Susceptible → Infected (transmission)",
                    "Infected → Treatment/AIDS (progression)", 
                    "All → Natural Death",
                    "AIDS → AIDS Death"
                ]
            },
            "covid_patterns": {
                "compartments": [
                    "Susceptible",
                    "Exposed", 
                    "Infectious (by severity/isolation status)",
                    "Hospitalized (by care level)",
                    "ICU",
                    "Recovered",
                    "Dead"
                ],
                "severity_stratification": ["presymptomatic", "mild to moderate", "severe", "isolated", "quarantined"],
                "key_parameters": ["transmission rates", "progression rates", "recovery rates", "death rates"],
                "flow_patterns": [
                    "Susceptible → Exposed (transmission)", 
                    "Exposed → Infectious (incubation)",
                    "Infectious → Recovery/Hospitalization/Death",
                    "Hospitalized → ICU/Recovery",
                    "ICU → Recovery/Death"
                ]
            }
        }
    
    def _load_metamodel(self, metamodel_path: str) -> Dict[str, Any]:
        """Load metamodel from JSON file"""
        try:
            with open(metamodel_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return basic metamodel if file doesn't exist
            return {"seirmodel_metamodel": {"compartment_types": {"epidemiological_states": ["Susceptible", "Exposed", "Infectious", "Recovered"]}}}
    
    def generate_extraction_prompt(self, paper_text: str) -> str:
        """Generate comprehensive prompt for extracting SEIR model from research paper"""
        
        # Include training examples
        examples_section = self.example_loader.get_examples_for_prompt()
        
        base_prompt = f"""
You are an expert epidemiologist tasked with extracting a SEIR epidemiological model from a research paper and converting it into a specific XML format.

{examples_section}

## NEW RESEARCH PAPER TO ANALYZE:
{paper_text}

## YOUR TASK:
Analyze the paper and create a SEIR model in XML format that captures the epidemiological structure described in the paper, following the patterns shown in the examples above.

## ANALYSIS GUIDELINES:

### 1. IDENTIFY COMPARTMENTS
Look for population states mentioned in the paper such as:
- **Disease states**: Susceptible, Exposed, Infectious, Recovered, Dead
- **Treatment states**: Treated, Hospitalized, ICU, Quarantined, Isolated  
- **Demographic groups**: Age groups, risk groups, gender, geographic regions
- **Disease progression**: Asymptomatic, Symptomatic, Mild, Moderate, Severe, Critical

### 2. IDENTIFY POPULATION STRATIFICATION
Determine if the model uses:
- **Risk-based stratification** (like HIV: MSM, heterosexual men, women)
- **Age-based stratification** (children, adults, elderly)
- **Severity-based stratification** (mild, moderate, severe cases)
- **Geographic stratification** (regions, cities, countries)
- **No stratification** (single population)

### 3. EXTRACT PARAMETERS AND RATES
Find numerical values for:
- **Transmission rates** (β, λ, contact rates)
- **Progression rates** (incubation, recovery, mortality)
- **Population sizes** (initial conditions)
- **Intervention effects** (vaccination, treatment, isolation)

### 4. MAP TRANSITIONS
Identify all flows between compartments:
- **Natural progression** (S→E→I→R)
- **Intervention effects** (vaccination, treatment, quarantine)
- **Mortality flows** (disease-specific and natural death)
- **Birth/recruitment flows** (population renewal)

## XML OUTPUT REQUIREMENTS:

### Structure:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<seir:SEIRModel xmi:version="2.0" xmlns:xmi="http://www.omg.org/XMI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:seir="http://example.com/seirmodel">
  <compartments PrimaryName="CompartmentType" SecondaryName="SpecificGroup">
    <outgoingFlows rate="numeric_value" target="//@compartments.index" description="flow_description"/>
  </compartments>
</seir:SEIRModel>
```

### Rules:
1. **PrimaryName**: Use standard epidemiological terms (Susceptible, Exposed, Infectious, Recovered, etc.)
2. **SecondaryName**: Use for population subgroups (optional, omit if no stratification)
3. **rate**: MUST be numeric values, not mathematical expressions
4. **target**: Use 0-based indexing (//@compartments.0, //@compartments.1, etc.)
5. **description**: Brief explanation of the transition

### Validation:
- Each compartment must have a unique (PrimaryName, SecondaryName) combination
- All rate values must be calculated numbers (e.g., 0.0275, 1.5E-5)
- Target indices must reference existing compartments
- Terminal compartments (Death, Recovered) typically have no outgoing flows

## EXAMPLES FROM EXISTING MODELS:

### HIV Model Pattern:
- Recruitment compartments for demographic groups
- Susceptible compartments stratified by risk group
- Infected compartments with treatment progression
- Terminal states for different death causes

### COVID Model Pattern:  
- Single susceptible population
- Exposed with optional quarantine
- Infectious stratified by severity and isolation
- Hospital/ICU care progression
- Single recovered and death states

## OUTPUT INSTRUCTIONS:
1. Generate ONLY the XML content
2. Calculate all mathematical expressions to numeric values
3. Ensure proper 0-based indexing for all target references
4. Include realistic rate values based on the paper's data
5. Use appropriate compartment names from the epidemiological literature

Generate the complete SEIR model XML now:
"""
        return base_prompt
    
    def generate_validation_prompt(self, generated_xml: str) -> str:
        """Generate prompt for validating and improving generated SEIR model"""
        
        validation_prompt = f"""
Review the following SEIR model XML and check for issues:

## GENERATED MODEL:
{generated_xml}

## VALIDATION CHECKLIST:

### 1. XML Structure
- ✓ Proper XML declaration and namespace
- ✓ All tags properly closed
- ✓ Valid attribute syntax

### 2. Compartments
- ✓ Reasonable epidemiological compartment names
- ✓ No duplicate (PrimaryName, SecondaryName) combinations
- ✓ Logical compartment progression

### 3. Flows
- ✓ All rates are numeric (not mathematical expressions)
- ✓ Target indices reference existing compartments
- ✓ Target indices are 0-based and within range
- ✓ Logical flow directions

### 4. Epidemiological Logic
- ✓ Realistic rate values
- ✓ Proper disease progression pathways
- ✓ Terminal compartments have no outgoing flows
- ✓ Model structure matches epidemiological principles

## RESPONSE FORMAT:
If issues found, provide:
1. List of specific errors
2. Corrected XML version
3. Brief explanation of changes

If no issues, respond: "VALIDATION PASSED"
"""
        return validation_prompt
    
    def get_metamodel_info(self) -> str:
        """Get metamodel information for prompt context"""
        try:
            compartment_types = []
            for category in self.metamodel["seirmodel_metamodel"]["compartment_types"].values():
                if isinstance(category, list):
                    compartment_types.extend(category)
            
            return f"""
## AVAILABLE COMPARTMENT TYPES:
{', '.join(compartment_types)}

## XML STRUCTURE REQUIREMENTS:
- Root: <seir:SEIRModel> with required namespaces
- Elements: <compartments> with PrimaryName (required) and SecondaryName (optional)
- Flows: <outgoingFlows> with rate (numeric), target (index), description (optional)
"""
        except:
            return "## Use standard epidemiological compartment types and proper XML structure."