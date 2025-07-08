import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
import PIL.Image




try:
    # Load the API key from environment variables
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(env_path)
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("FATAL ERROR: 'GOOGLE_API_KEY' environment variable not set.")
    print("Please set it before running the script.")
    exit()
model = genai.GenerativeModel('gemini-1.5-flash-latest')








def generate_seirmodel_from_image(image_path: str, user_input: str, langSpecs_path: str, output_fileName: str) -> str:
    """
    Generates a response from a multimodal prompt including text and an image,
    then saves the full interaction to a file.
    """
    try:
        # Load the language specifications
        with open(langSpecs_path, "r", encoding="utf-8") as f:
            lang_specs = f.read()
        
        # Load the image using the modern PIL library
        img = PIL.Image.open(image_path)

    except FileNotFoundError as err:
        print(f"Error: A required file was not found - {err}")
        return f"Error: A required file was not found - {err}"
    except Exception as err:
        print(f"An unexpected error occurred while reading files: {err}")
        return f"An unexpected error occurred while reading files: {err}"


    print(f"Image loaded successfully from '{image_path}'.")
    # --- Construct the final prompt text ---
    separator = "\n" + "*" * 80 + "\n"


    llm1_input = (
        f"{separator}"
        f"PROMPT: \n{LLM1_PROMPT}\n"
        f"{separator}"
        f"METAMODEL: \n{lang_specs}\n"
        f"{separator}"
        f"Data:\n{user_input}"
    )

    llm1 = model.generate_content([
        img,                 # The image object
        llm1_input.strip()  # The text part of the prompt
    ]).text.strip()


    llm2_input = (
        f"{separator}"
        f"PROMPT:\n{LLM2_PROMPT.strip()}\n"
        f"{separator}"
        f"USER INPUT:\n{user_input.strip()}\n"
        f"{separator}"
        f"STRUCTURALLY CORRECT SEIRMODEL FILE:\n{llm1.strip()}\n"
        f"{separator}"
    )

    # --- Call the modern API with a list of parts (image and text) ---
    llm2 = model.generate_content(llm2_input.strip()).text.strip()
    
    # --- Format and save the output ---
    output_content =(
        f"LLM1 PROMPT:\n{LLM1_PROMPT}"
        f"{separator}"
        f"METAMODEL, USER INPUT AND IMAGE"
        f"{separator}"
        f"LLM1 RESPONSE:\n {llm1}"
        f"{separator}"
        f"LLM2 PROMPT:\n{LLM2_PROMPT}"
        f"{separator}"
        f"USER INPUT:\n{user_input}"
        f"{separator}"
        f"LLM2'S RESPONSE:\n{llm2}"
    )

    try:
        # Ensure the output directory exists
        output_dir = os.path.join(os.path.dirname(output_fileName), "prompt_sample")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, os.path.basename(output_fileName))
        with open(output_file, "w", encoding="utf-8") as tf:
            tf.write(output_content)
    except IOError as e:
        return f"Error writing to output file '{output_fileName}': {e}"

    return f"SEIR model successfully written to {output_fileName}"






# Constants for prompts and file names
EMPTY_PROMPT = "No Parameters provided, use the provided image to get the useful informations."

PROMPT_FOR_TEXT = """
You are now responsible for generating a complete SEIR model XML file using only the provided user input and XML language specification.
Do not assume any external context or missing information. Everything you need has already been provided.

You have access to:
- user_input: This includes all necessary compartment types, groups, and flows.
- language_specification: A skeleton XML that defines structure and format. Follow it exactly. Do not alter required lines.

Your output must be:
1. A valid and complete XML file in the format shown in the skeleton.
2. Use only the information given in user_input.
3. Output ONLY the XML file — no extra comments, notes, formatting, or text outside the XML.
4. If something is unclear, use a placeholder value with a comment like <!-- missing info -->.
5. The output will be parsed by a strict system. Maintain clean structure and formatting.
"""

PROMPT_WITH_IMAGE = """
You are now responsible for generating a complete SEIR model XML file using only the provided user input, image and language specification/metamodel of seirmodel.
Do not assume any external context or missing information. Everything you need has already been provided.

- model_diagram (image): This shows all compartments and directional flows.
- user_input (text): Provides parameter values, population numbers, and formulas.
- language_specification/metamodel (text): Make use of this file to understand the required XML structure and elements.

Instructions:
1. Extract compartments and transitions from the image (left to right, top-down if needed).
2. Use `user_input` to fill rates, formulas, and initial values.
3. Follow the XML structure exactly. No extra text or formatting.
4. Use 0-based indexing for compartments in order of appearance.
5. If any info is unclear, use `<!-- missing info -->` as placeholder.

Only return the final XML file.
"""


LLM1_PROMPT = """
You are an expert in XML structure generation for epidemiological models.

Your task is to generate a structurally correct SEIR model in XML format using the provided **model diagram (image)** and **language specification/metamodel**.

You must:
- Focus ONLY on generating compartment and flow structure.
- DO NOT attempt to calculate or insert any numeric rate values.
- Instead, use a placeholder `[[rate_missing]]` for all `rate` attributes that require computation later.
- Use 0-based indexing for compartments in the order they appear (top-down, left-to-right).
- Follow the metamodel strictly for element names, attributes, and nesting.
- Include all compartments and their directional flows shown in the diagram.

Inputs:
- model_diagram (image): Shows compartments and directional transitions.
- language_specification (text): Defines the structure and rules for valid SEIR XML.

Output:
- Only the final XML file. Do not include explanations or markdown formatting.
- Ensure all required attributes are present and validate against the provided metamodel.
"""

LLM2_PROMPT = """
You are an expert at interpreting epidemiological equations and inserting computed rates into XML model files.

You are given:
1. A partially completed SEIR XML file, where all rate fields are marked as [[rate_missing]].
2. A user_input section that includes all relevant parameter values, formulas, and population data.

YOUR TASK:
1. Identify each [[rate_missing]] inside an <outgoingFlows> tag.
2. Use the description and flow direction (source → target) to determine which rate formula applies.
3. Compute the rate using the correct formula and values:
  - For contact-based flows, convert to a rate using population values.
  - Substitute variables directly from the data.
  - Never assume missing values unless they are explicitly derivable.
4. Before writing the rate, first add a detailed comment explaining your full reasoning.
5. Then insert the final computed value as the rate.

IMPORTANT RULES:
- Do not round — use full numerical precision at all times.
- Do not modify the XML structure or tags.
- If a rate cannot be computed (due to missing data), leave a clear comment:
    `<!-- missing due to undefined variable: βm -->`

How to Write Reasoning (Baby-Step Style):
  For each <outgoingFlows> you process:
    First, add a full step-by-step comment above the rate:
      - Use simple language, no skipped math
      - Treat it like teaching someone new to equations
      - Explain each substitution and operation clearly
      - Then, insert the rate based on that computation.
  Example:

        <!-- We are using the formula: a × b × (c - 1)
             Step 1: a = 2
             Step 2: b = 3
             Step 3: c = 4, so (c - 1) = 3
             Step 4: Multiply: 2 × 3 = 6
             Step 5: Then: 6 × 3 = 18
             Therefore, the rate is 18 -->
      <outgoingFlows rate="18" target="//@compartments.3">
      </outgoingFlows>


Final Note: Your only task is to calculate and insert correct rate values. Please Do not add, remove, or reorder compartments or flows. Also don't change the target parameter in any ongoingrate tag.
"""


PROMPT_EXTRACT_PARAMETERS = """
You are an expert at extracting epidemiological model parameters from research data.
Given the diagram, user-provided data, and metadata, extract a table of all parameters.

Each parameter must include: 
- Source compartment
- Target compartment
- Equation (if applicable)
- Final value (if computable)
- Comments (provide you reasoning in detail, why did you come up with this value.)\n\n
- Respond ONLY with a description and a clear markdown table.
Note that your input will be used to generate a SEIR model, however my platform doesnt support contact based flow so you need to calculate then as rate based (used the inital population value rather than function).
Do not round any numerical values. Always show the full computed result with maximum precision.
"""


LANG_SPECS_FILENAME = "seirmodel_skeleton.txt"
METAMODEL_FILENAME = "metamodel.txt"
METAMODEL_SKELETON_FILENAME = "metamodel_skeleton_seirmodel.txt"


#User Input
hiv_json = """
[{'compartment_index': 0,
  'PrimaryName': 'Recruitment',
  'SecondaryName': 'Homosexual Men',
  'outgoingFlows': [{'rate': '12.7872',
    'description': '𝛹𝜃(1−𝛾)',
    'target': '//@compartments.3'}]},
 {'compartment_index': 1,
  'PrimaryName': 'Recruitment',
  'SecondaryName': 'Women',
  'outgoingFlows': [{'rate': '173.16',
    'description': '𝛹(1−𝜃)',
    'target': '//@compartments.4'}]},
 {'compartment_index': 2,
  'PrimaryName': 'Recruitment',
  'SecondaryName': 'Heterosexual Men',
  'outgoingFlows': [{'rate': '147.0528',
    'description': '𝛹𝜃𝛾',
    'target': '//@compartments.5'}]},
 {'compartment_index': 3,
  'PrimaryName': 'Susceptible',
  'SecondaryName': 'Homosexual Men',
  'outgoingFlows': [{'rate': '0.09636',
    'description': 'λh',
    'target': '//@compartments.6'},
   {'rate': '0.0129', 'description': 'μ', 'target': '//@compartments.12'}]},
 {'compartment_index': 4,
  'PrimaryName': 'Susceptible',
  'SecondaryName': 'Women',
  'outgoingFlows': [{'rate': '1.637E-5',
    'description': 'λhw (From Homosexual Man) ',
    'target': '//@compartments.7'},
   {'rate': '1.355E-5',
    'description': 'λm (Form Woman)',
    'target': '//@compartments.7'},
   {'rate': '0.0129', 'description': 'μ ', 'target': '//@compartments.12'}]},
 {'compartment_index': 5,
  'PrimaryName': 'Susceptible',
  'SecondaryName': 'Heterosexual Men',
  'outgoingFlows': [{'rate': '2.5E-6',
    'description': 'λw (From Heterosexual Man)',
    'target': '//@compartments.8'},
   {'rate': '1.1368E-4',
    'description': 'λhm (From Homosexual Man)',
    'target': '//@compartments.8'},
   {'rate': '0.0129', 'description': 'μ', 'target': '//@compartments.12'}]},
 {'compartment_index': 6,
  'PrimaryName': 'Untreated Infected',
  'SecondaryName': 'Homosexual Men',
  'outgoingFlows': [{'rate': '0.0129',
    'description': 'μ',
    'target': '//@compartments.12'},
   {'rate': '0.29997', 'description': 'α * p', 'target': '//@compartments.9'},
   {'rate': '0.03333',
    'description': '1-p * α',
    'target': '//@compartments.10'}]},
 {'compartment_index': 7,
  'PrimaryName': 'Untreated Infected',
  'SecondaryName': 'Women',
  'outgoingFlows': [{'rate': '0.0129',
    'description': 'μ',
    'target': '//@compartments.12'},
   {'rate': '0.29997', 'description': 'p * α', 'target': '//@compartments.9'},
   {'rate': '0.03333',
    'description': 'α * 1-p',
    'target': '//@compartments.10'}]},
 {'compartment_index': 8,
  'PrimaryName': 'Untreated Infected',
  'SecondaryName': 'Heterosexual Men',
  'outgoingFlows': [{'rate': '0.0129',
    'description': 'μ',
    'target': '//@compartments.12'},
   {'rate': '0.29997', 'description': 'p * α', 'target': '//@compartments.9'},
   {'rate': '0.03333',
    'description': '1-p * α',
    'target': '//@compartments.10'}]},
 {'compartment_index': 9,
  'PrimaryName': 'Treated with ART',
  'SecondaryName': '',
  'outgoingFlows': [{'rate': '0.018',
    'description': 'δ',
    'target': '//@compartments.10'},
   {'rate': '0.0129', 'description': 'μ', 'target': '//@compartments.12'}]},
 {'compartment_index': 10,
  'PrimaryName': 'People living with AIDS',
  'SecondaryName': '',
  'outgoingFlows': [{'rate': '0.3333',
    'description': 'd',
    'target': '//@compartments.11'},
   {'rate': '0.0129', 'description': 'μ', 'target': '//@compartments.12'}]},
 {'compartment_index': 11,
  'PrimaryName': 'Death due to AIDS',
  'SecondaryName': '',
  'outgoingFlows': []},
 {'compartment_index': 12,
  'PrimaryName': 'Natural Death',
  'SecondaryName': '',
  'outgoingFlows': []}]
"""

hiv_all_info = """

Compartment Names with indexes:
0. Recruitment (Homosexual Men)
1. Recruitment (Women)
2. Recruitment (Heterosexual Men)
3. Susceptible (Homosexual Men)
4. Susceptible (Women)
5. Susceptible (Heterosexual Men)
6. Untreated Infected (Homosexual Men)
7. Untreated Infected (Women)
8. Untreated Infected (Heterosexual Men)
9. Treated with ART
10. People living with AIDS
11. Death due to AIDS
12. Natural Death


Flow direction and their parameters values:
Recruitment → Susceptible (Homosexual Men): 333 * 0.48 * (1 - 0.92) = 12.7872
Recruitment → Susceptible (Women): 333 * (1 - 0.48) = 173.16
Recruitment → Susceptible (Heterosexual Men): 333 * 0.48 * 0.92 = 147.0528

Susceptible (Homosexual Men) → Untreated Infected (Homosexual Men): λh = 0.44 * 7 * 79 / (2446 + 79) ≈ 0.09636
Susceptible (Homosexual Men) → Natural Death: μ = 0.0129

Susceptible (Women) → Untreated Infected (Women):  
- λhw (from homosexual men) = 0.018 * 2 * 79 / (2446 + 171173 + 79 + 29) ≈ 1.637E-5  
- λm (from women) = 0.02 * 4 * 6 / (189994 + 6) ≈ 1.355E-5  
Susceptible (Women) → Natural Death: μ = 0.0129

Susceptible (Heterosexual Men) → Untreated Infected (Heterosexual Men):  
- λw (from heterosexual men) = 0.02 * 4 * 29 / (171173 + 29) ≈ 2.5E-6  
- λhm (from homosexual men) = 0.25 * 1 * 79 / (2446 + 171173 + 79 + 29) ≈ 1.1368E-4  
Susceptible (Heterosexual Men) → Natural Death: μ = 0.0129

Untreated Infected → Treated with ART: α * p = 0.3333 * 0.9 = 0.29997  
Untreated Infected → People living with AIDS: α * (1 - p) = 0.3333 * 0.1 = 0.03333  
Untreated Infected → Natural Death: μ = 0.0129

Treated with ART → People living with AIDS: δ = 0.018  
Treated with ART → Natural Death: μ = 0.0129

People living with AIDS → Death due to AIDS: d = 0.3333  
People living with AIDS → Natural Death: μ = 0.0129
"""

hiv_imp_info_only = """
| Index | Compartment                        | Subgroup         |
| ----- | ---------------------------------- | ---------------- |
| 0     | Recruitment_HomosexualMen          | Homosexual Men   |
| 1     | Recruitment_Women                  | Women            |
| 2     | Recruitment_HeterosexualMen        | Heterosexual Men |
| 3     | Susceptible_HomosexualMen          | Homosexual Men   |
| 4     | Susceptible_Women                  | Women            |
| 5     | Susceptible_HeterosexualMen        | Heterosexual Men |
| 6     | UntreatedInfected_HomosexualMen    | Homosexual Men   |
| 7     | UntreatedInfected_Women            | Women            |
| 8     | UntreatedInfected_HeterosexualMen  | Heterosexual Men |
| 9     | TreatedWithART                     | Shared           |
| 10    | PeopleLivingWithAIDS               | Shared           |
| 11    | DeathDueToAIDS                     | Terminal         |
| 12    | NaturalDeath                       | Terminal         |


| Flow (From → To)                                            | Rate Variable   |
| ----------------------------------------------------------- | --------------- |
| Recruitment_HomosexualMen → Susceptible_HomosexualMen       | Ψ × θ × (1 − γ) |
| Recruitment_Women → Susceptible_Women                       | Ψ × (1 − θ)     |
| Recruitment_HeterosexualMen → Susceptible_HeterosexualMen   | Ψ × θ × γ       |
| Susceptible_HomosexualMen → UntreatedInfected_HomosexualMen  | λh              |
| Susceptible_Women → UntreatedInfected_Women    (homosexual men and women)              | λhw         |
| Susceptible_Women → UntreatedInfected_Women  (Heterosexual)                | λm         |
| Susceptible_HeterosexualMen → UntreatedInfected_HeterosexualMen (homosexual men and heterosexual) | λhm         |
| Susceptible_HeterosexualMen → UntreatedInfected_HeterosexualMen  (heterosexual) | λw      |
| UntreatedInfected_HomosexualMen → TreatedWithART                          | α × p           |
| UntreatedInfected_Women → TreatedWithART                          | α × p           |
| UntreatedInfected_HeterosexualMen → TreatedWithART                          | α × p           |
| UntreatedInfected_HomosexualMen → PeopleLivingWithAIDS                    | α × (1 − p)     |
| UntreatedInfected_Women → PeopleLivingWithAIDS                    | α × (1 − p)     |
| UntreatedInfected_HeterosexualMen → PeopleLivingWithAIDS                    | α × (1 − p)     |
| TreatedWithART → PeopleLivingWithAIDS                       | δ               |
| PeopleLivingWithAIDS → DeathDueToAIDS                       | d               |
| All states → NaturalDeath                                   | μ               |

lamda flow equations:
λh = βh * ch * (Ih / (Sh + Ih))
λhw = βhw * Chw * (Ih / (Sm + Sh + Im + Ih))
λhm = βhm * Chm * (Ih / (Sm + Sh + Im + Ih))
λm = βs * cs * (Iw / (Sw + Iw))
λw = βs * cs * (Im / (Sm + Im)) 

Data of all the parameters is as follows(only use the necceassary values):
Ψ	333	
θ	0.48	
γ	0.92	
p	0.90	
μ	0.0129	
d	0.3333	
δ	0.018	
α	0.3333	
βs	0.02	
βh	0.44	
βhw	0.018	
βhm	0.25	
cs	4	
ch	7	
Chw	2	
Chm	1	

Populations parameters are(only use the necceassary values):
Sℎ	=2⁢4⁢4⁢6,	𝐼ℎ	=7⁢9,	𝑆𝑤	=1⁢8⁢9⁢9⁢9⁢4,	𝐼𝑤	=6,
𝑆𝑚	=1⁢7⁢1⁢1⁢7⁢3,	𝐼𝑚	=2⁢9,	𝑇	=1⁢0⁢7,	𝐴	=4⁢7.

"""

covidModel = """
| Index | Compartment Name                        |
| ----- | --------------------------------------- |
| 0     | Susceptible                             |
| 1     | Exposed                                 |
| 2     | Exposed (quarantined)                   |
| 3     | Infectious (presymptomatic)             |
| 4     | Infectious (presymptomatic, isolated)   |
| 5     | Infectious (mild to moderate)           |
| 6     | Infectious (severe)                     |
| 7     | Infectious (mild to moderate, isolated) |
| 8     | Infectious (severe, isolated)           |
| 9     | Isolated                                |
| 10    | Recovered                               |
| 11    | Admitted to hospital                    |
| 12    | Admitted to hospital (pre-ICU)          |
| 13    | Admitted to hospital (post-ICU)         |
| 14    | ICU                                     |
| 15    | Dead                                    |

| From → To                                      | Description                      | Rate / Parameter |
| ---------------------------------------------- | -------------------------------- | ---------------- |
| Susceptible → Exposed                          | Infection                        | 0.0276           |
| Susceptible → Exposed (quarantined)            | Infection (quarantine pathway)   | 0.0031           |
| Exposed → Infectious (presymptomatic)          | End of latency                   | 0.4              |
| Exposed (quarantined) → Infectious (iso)       | End of latency (isolated)        | 0.4              |
| Infectious (presymptomatic) → Mild/Mod         | Develops symptoms                | 0.97             |
| Infectious (presymptomatic) → Severe           | Becomes severely ill             | 0.03             |
| Infectious (presymp, isolated) → Mild/Mod, iso | Develops symptoms (in isolation) | 0.97             |
| Infectious (presymp, isolated) → Severe, iso   | Becomes severe (in isolation)    | 0.03             |
| Mild/Mod → Hospitalization                     | Worsening condition              | 0.4              |
| Mild/Mod → Recovered                           | Recovery                         | 0.167            |
| Severe → Hospital (general)                    | Hospital admission               | 0.167            |
| Severe → Hospital (pre-ICU)                    | Critical admission               | 0.167            |
| Mild/Mod, isolated → Recovered                 | Recovery (isolated)              | 0.167            |
| Severe, isolated → Hospital (pre-ICU)          | Critical admission (isolated)    | 0.167            |
| Severe, isolated → Hospital (general)          | Hospital admission (isolated)    | 0.167            |
| Isolated → Recovered                           | Recovery from isolation          | 0.167            |
| Hospital → Recovered                           | Recovered from care              | 0.1              |
| Hospital (pre-ICU) → ICU                       | Worsens to ICU                   | 0.087            |
| Hospital (post-ICU) → Recovered                | Recovered after ICU              | 0.048            |
| ICU → Dead                                     | Death in ICU                     | 0.0095           |
| ICU → Hospital (post-ICU)                      | Survived ICU                     | 0.038            |

"""

simpleModel_imp_info_only = """
| Index | Primary Name    | Description                           |
| ----- | --------------- | ------------------------------------- |
| 0     | Susceptible (S) | Individuals who can be infected       |
| 1     | Exposed (E)     | Infected but not yet infectious       |
| 2     | Infectious (I)  | Capable of transmitting the infection |
| 3     | Recovered (R)   | Immune but may lose immunity later    |


| From → To   | Description             | Rate Expression / Parameter |
| ----------- | ----------------------- | --------------------------- |
| S → E       | Infection               | **βSI/N**                   |
| E → I       | End of latency          | **σE**                      |
| I → R       | Recovery                | **γI**                      |
| R → S       | Loss of immunity        | **ωR**                      |
| All → death | Background mortality    | **µ** for each compartment  |
| I → null    | Infection-induced death | **αI**                      |
| ∅ → S       | Birth into Susceptible  | **µN**                      |


| Parameter | Meaning                                          | Value (from paper)                   |
| --------- | ------------------------------------------------ | ------------------------------------ |
| β         | Contact (transmission) rate                      | **0.21/day**                         |
| γ         | Recovery rate (1/γ is infectious period)         | **1/14 days** → γ ≈ **0.0714/day**   |
| σ         | Latency rate (1/σ is incubation period)          | **1/7 days** → σ ≈ **0.143/day**     |
| ω         | Immunity loss rate (1/ω is duration of immunity) | **1/365 days** → ω ≈ **0.00274/day** |
| µ         | Background birth/death rate                      | **1/76 years** → µ ≈ **3.6e-5/day**  |
| α         | Infection-induced mortality rate                 | **0** (assumed zero for this model)  |

"""


