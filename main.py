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



def generate_seirmodel(prompt: str, user_input: str, langSpecs_path: str, output_fileName: str) -> str: 
    with open(langSpecs_path, "r", encoding="utf-8") as f:
        lang_specs = f.read()

    separator = "\n" + "*" * 80 + "\n"
    final_prompt = (
        f"{separator}"
        f"PROMPT:\n{prompt.strip()}\n"
        f"{separator}"
        f"USER INPUT:\n{user_input.strip()}\n"
        f"{separator}"
        f"LANGUAGE SPECIFICATION:\n{lang_specs.strip()}\n"
        f"{separator}"
    )

    response = model.generate_content(final_prompt)

    

    output = f"{final_prompt}{separator}RESPONSE:\n{response.text.strip()}\n"

    # Ensure the output directory exists
    output_dir = os.path.join(os.path.dirname(output_fileName), "prompt_sample")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, os.path.basename(output_fileName))
    with open(output_file, "w", encoding="utf-8") as tf:
      tf.write(output)

    return f"SEIR model successfully written to {output_fileName}"
    
def generate_seirmodel_from_image(prompt: str, image_path: str, user_input: str, langSpecs_path: str, output_fileName: str) -> str:
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

    except FileNotFoundError as e:
        return f"Error: A required file was not found - {e}"
    except Exception as e:
        return f"An unexpected error occurred while reading files: {e}"


    print(f"Image loaded successfully from '{image_path}'.")
    # --- Construct the final prompt text ---
    separator = "\n" + "*" * 80 + "\n"
    final_prompt_text = (
        f"{separator}"
        f"PROMPT:\n{prompt.strip()}\n"
        f"{separator}"
        f"USER INPUT:\n{user_input.strip()}\n"
        f"{separator}"
        f"LANGUAGE SPECIFICATION:\n{lang_specs.strip()}\n"
        f"{separator}"
    )

    # --- Call the modern API with a list of parts (image and text) ---
    response = model.generate_content([
        img,                 # The image object
        final_prompt_text.strip()  # The text part of the prompt
    ])
    
    # --- Format and save the output ---
    output_content = f"{final_prompt_text}RESPONSE:\n{response.text.strip()}\n"

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
You are responsible for generating a valid SEIR model XML file using:

- model_diagram (image): This shows all compartments and directional flows.
- user_input (text): Provides parameter values, population numbers, and formulas.
- language_specification (text): Defines strict XML structure. Do not change required lines.

Instructions:
1. Extract compartments and transitions from the image (left to right, top-down if needed).
2. Use `user_input` to fill rates, formulas, and initial values.
3. Follow the XML structure exactly. No extra text or formatting.
4. Use 0-based indexing for compartments in order of appearance.
5. If any info is unclear, use `<!-- missing info -->` as placeholder.

Only return the final XML file.
"""

LANG_SPECS_FILENAME = "seirmodel_skeleton.txt"


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
We consider a population split into three risk groups: homosexual men, heterosexual men, and women. Each group starts in the "Susceptible" compartment and may transition to "Untreated Infected", then to "Treated with ART" or "People living with AIDS", and finally either to "Death due to AIDS" or "Natural Death".
Note that 𝐵ℎ,ℎ⁢𝑤,ℎ⁢𝑚,𝑠 represents the product between the probability of contagion 𝛽ℎ,ℎ⁢𝑤,ℎ⁢𝑚,𝑠 and the rate of the number of sexual partners, 𝑐ℎ,ℎ⁢𝑤,ℎ⁢𝑚,𝑠.
Recruitment into the population occurs at different rates:
- Homosexual men: 𝛹 * 𝜃 * (1−𝛾)
- Women: 𝛹 * (1−𝜃)
- Heterosexual men: 𝛹 * 𝜃 * 𝛾

Susceptible individuals become infected at different rates depending on exposure:
- Homosexual men: λh = βh * ch * Ih/(Sh+Ih)
- Women: λhw (from homosexual men) = βhw * chw * Ih/(Sh+ Sm + Ih + Im), λm (from women)  = βs * cs * Iw/(Sw + Iw)
- Heterosexual men: λw (from heterosexual men) = βs * cs * Im/(Sm + Im), λhm (from homosexual men) = βhm * chm * Ih/(Sh+ Sm + Ih + Im)

All individuals are subject to a natural death rate μ.

The following compartments and their transition are not gender-specific but apply to all groups do not create seperate compartment for each gender just one and so no need to use secondary compartment:
Untreated infected individuals progress to either:
- Treatment: with rate α * p
- AIDS: with rate (1 - p) * α

Treated individuals may still progress to AIDS at rate δ or die naturally.

People living with AIDS may:
- Die due to AIDS at rate d
- Die naturally at rate μ



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


There are two terminal compartments: Death due to AIDS and Natural Death.
"""


# LLM in action
generate_seirmodel(
  prompt=PROMPT_FOR_TEXT,
  user_input=hiv_json,
  langSpecs_path=LANG_SPECS_FILENAME,
  output_fileName="hiv_json.txt"
)
time.sleep(20)

generate_seirmodel(
  prompt=PROMPT_FOR_TEXT,
  user_input=hiv_all_info,
  langSpecs_path=LANG_SPECS_FILENAME,
  output_fileName="hiv_all_info.txt"
)
time.sleep(20)

generate_seirmodel(
  prompt=PROMPT_FOR_TEXT,
  user_input=hiv_imp_info_only,
  langSpecs_path=LANG_SPECS_FILENAME,
  output_fileName="hiv_imp_info_only.txt"
)

time.sleep(20)  

generate_seirmodel_from_image(
  prompt=PROMPT_WITH_IMAGE,
  image_path="hivModel(epimde).jpg",
  user_input=hiv_imp_info_only,
  langSpecs_path=LANG_SPECS_FILENAME,
  output_fileName="hiv_image_with_table.txt"
)
time.sleep(20)

generate_seirmodel_from_image(
  prompt=PROMPT_WITH_IMAGE,
  image_path="hivModel(epimde).jpg",
  user_input=EMPTY_PROMPT,
  langSpecs_path=LANG_SPECS_FILENAME,
  output_fileName="hiv_only_image.txt"
)

time.sleep(20)

generate_seirmodel_from_image(
  prompt=PROMPT_WITH_IMAGE,
  image_path="HIV(Unorganized).jpg",
  user_input=hiv_imp_info_only,
  langSpecs_path=LANG_SPECS_FILENAME,
  output_fileName="hiv_img(unorganized).txt"
)