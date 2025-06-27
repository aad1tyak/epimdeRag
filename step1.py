from cohere import ClientV2
import os
import google.generativeai as genai
import PIL.Image

co = ClientV2("ZPbb7mQFHRaNyASPn9GaPWqE3XLT0bminHhkYqhk")

try:
    # Load the API key from environment variables
    genai.configure(api_key="AIzaSyAvEgt_vD5Tuf3d1yStxkYWv9mjAGjQ6Uk")
except KeyError:
    print("FATAL ERROR: 'GOOGLE_API_KEY' environment variable not set.")
    print("Please set it before running the script.")
    exit()
model = genai.GenerativeModel('gemini-1.5-flash-latest')



def generate_seirmodel(prompt: str, user_input: str, langSpecs_path: str, output_path: str) -> str: 
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

    response = co.chat(
        model="command-a-03-2025",
        messages=[{"role": "user", "content": final_prompt}]
    )

    # Correct way to access content in ClientV2 response
    content_blocks = response.message.content  # Not a dict, it's a list of Text blocks

    if not content_blocks or not isinstance(content_blocks, list):
        return "Issue: response content is missing or not a list."

    # Assume first block is the XML output
    text = content_blocks[0].text.strip()

    output = f"{final_prompt}{separator}RESPONSE:\n{text}\n"

    with open(output_path, "w", encoding="utf-8") as tf:
        tf.write(output)

    return f"SEIR model successfully written to {output_path}"
    
def generate_seirmodel_from_image(prompt: str, image_path: str, user_input: str, langSpecs_path: str, output_path: str) -> str:
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
    print(f"Sending request for '{output_path}' to the Gemini API...")
    response = model.generate_content([
        img,                 # The image object
        final_prompt_text.strip()  # The text part of the prompt
    ])
    
    # --- Format and save the output ---
    output_content = f"{final_prompt_text}RESPONSE:\n{response.text.strip()}\n"

    try:
        with open(output_path, "w", encoding="utf-8") as tf:
            tf.write(output_content)
    except IOError as e:
        return f"Error writing to output file '{output_path}': {e}"

    return f"SEIR model successfully written to {output_path}"


PROMPT_ONLY_TEXT = """
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

Empty_PROMPT = "No Parameters provided, use the provided image to get the useful informations."

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

hiv_user_input = """
Follow the following order for compartments and target indices:
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

Flows:
Recruitment(Homosexual Men) → Susceptible (Homosexual Men): Ψ * θ * (1−γ)
Recruitment(Women) → Susceptible (Women): Ψ * (1−θ)
Recruitment(Heterosexual Men) → Susceptible (Heterosexual Men): Ψ * θ * γ

Susceptible (Homosexual Men) → Untreated Infected (Homosexual Men): λh
Susceptible (Homosexual Men) → Natural Death: μ

Susceptible (Women) → Untreated Infected (Women): λhw (from homosexual men), λm (from women)
Susceptible (Women) → Natural Death: μ

Susceptible (Heterosexual Men) → Untreated Infected (Heterosexual Men): λw (from heterosexual men), λhm (from homosexual men)
Susceptible (Heterosexual Men) → Natural Death: μ

Untreated Infected → Treated with ART: α * p
Untreated Infected → People living with AIDS: α * (1 − p)
Untreated Infected → Natural Death: μ

Treated with ART → People living with AIDS: δ
Treated with ART → Natural Death: μ

People living with AIDS → Death due to AIDS: d
People living with AIDS → Natural Death: μ

Parameters values:
Ψ = 333	
θ = 0.48	
γ = 0.92	
p = 0.90	
μ = 0.0129	
d = 0.3333	
δ = 0.018	
α = 0.3333
Infection rates:
- λh = 0.44 * 7 * 79 / (2446 + 79)
- λhw = 0.018 * 2 * 79 / (2446 + 171173 + 79 + 29)
- λm = 0.02 * 4 * 6 / (189994 + 6)
- λw = 0.02 * 4 * 29 / (171173 + 29)
- λhm = 0.25 * 1 * 79 / (2446 + 171173 + 79 + 29)

"""

simplified_hiv_user_input = """
[
  {
    "PrimaryName": "Recruitment",
    "SecondaryName": "Homosexual Men",
    "Flows": [
      {
        "rate": 12.7872,
        "target_index": 3,
        "description": "Ψ * θ * (1−γ)"
      }
    ]
  },
  {
    "PrimaryName": "Recruitment",
    "SecondaryName": "Women",
    "Flows": [
      {
        "rate": 173.16,
        "target_index": 4,
        "description": "Ψ * (1−θ)"
      }
    ]
  },
  {
    "PrimaryName": "Recruitment",
    "SecondaryName": "Heterosexual Men",
    "Flows": [
      {
        "rate": 147.0528,
        "target_index": 5,
        "description": "Ψ * θ * γ"
      }
    ]
  },
  {
    "PrimaryName": "Susceptible",
    "SecondaryName": "Homosexual Men",
    "Flows": [
      {
        "rate": 0.09636,
        "target_index": 6,
        "description": "λh"
      },
      {
        "rate": 0.0129,
        "target_index": 12,
        "description": "μ"
      }
    ]
  },
  {
    "PrimaryName": "Susceptible",
    "SecondaryName": "Women",
    "Flows": [
      {
        "rate": 0.00001637,
        "target_index": 7,
        "description": "λhw"
      },
      {
        "rate": 0.00001355,
        "target_index": 7,
        "description": "λm"
      },
      {
        "rate": 0.0129,
        "target_index": 12,
        "description": "μ"
      }
    ]
  },
  {
    "PrimaryName": "Susceptible",
    "SecondaryName": "Heterosexual Men",
    "Flows": [
      {
        "rate": 0.0000025,
        "target_index": 8,
        "description": "λw"
      },
      {
        "rate": 0.00011368,
        "target_index": 8,
        "description": "λhm"
      },
      {
        "rate": 0.0129,
        "target_index": 12,
        "description": "μ"
      }
    ]
  },
  {
    "PrimaryName": "Untreated Infected",
    "SecondaryName": "Homosexual Men",
    "Flows": [
      {
        "rate": 0.0129,
        "target_index": 12,
        "description": "μ"
      },
      {
        "rate": 0.29997,
        "target_index": 9,
        "description": "α * p"
      },
      {
        "rate": 0.03333,
        "target_index": 10,
        "description": "α * (1-p)"
      }
    ]
  },
  {
    "PrimaryName": "Untreated Infected",
    "SecondaryName": "Women",
    "Flows": [
      {
        "rate": 0.0129,
        "target_index": 12
      },
      {
        "rate": 0.29997,
        "target_index": 9
      },
      {
        "rate": 0.03333,
        "target_index": 10
      }
    ]
  },
  {
    "PrimaryName": "Untreated Infected",
    "SecondaryName": "Heterosexual Men",
    "Flows": [
      {
        "rate": 0.0129,
        "target_index": 12
      },
      {
        "rate": 0.29997,
        "target_index": 9
      },
      {
        "rate": 0.03333,
        "target_index": 10
      }
    ]
  },
  {
    "PrimaryName": "Treated with ART",
    "SecondaryName": "",
    "Flows": [
      {
        "rate": 0.018,
        "target_index": 10,
        "description": "δ"
      },
      {
        "rate": 0.0129,
        "target_index": 12,
        "description": "μ"
      }
    ]
  },
  {
    "PrimaryName": "People living with AIDS",
    "SecondaryName": "",
    "Flows": [
      {
        "rate": 0.3333,
        "target_index": 11,
        "description": "d"
      },
      {
        "rate": 0.0129,
        "target_index": 12,
        "description": "μ"
      }
    ]
  },
  {
    "PrimaryName": "Death due to AIDS",
    "SecondaryName": ""
  },
  {
    "PrimaryName": "Natural Death",
    "SecondaryName": ""
  }
]
"""

covid_user_input = """
I’m modeling COVID-19 dynamics with a detailed compartmental approach. The model starts with a Susceptible population, some of whom get exposed at rate β (contact transmission), while a fraction gets quarantined if detected early.

Exposed individuals transition to a presymptomatic infectious stage at rate σ. Some are isolated if already under quarantine. Presymptomatic individuals can either develop symptoms (probability p_s) or recover directly if mild.

Infectious compartments include:
- Presymptomatic (Ip)
- Mild/moderate (Imm)
- Severe (Is)
- Isolated versions of the above where applicable.

Mild/moderate cases either recover at rate γ₁ or progress to more severe infection at rate γ₂. Severe infections may lead to hospitalization or ICU, with transitions at rates δ₁ and δ₂. ICU patients either recover (rate ρ) or die (rate μ).

Hospital states include pre-ICU, post-ICU, and general admission. Isolation and quarantine modify transition dynamics but not the core disease path.

I’m using average parameter estimates from early COVID studies:
- β = 0.0276 (infection)
- σ = 0.4 (incubation)
- γ₁ = 0.167 (mild recovery)
- γ₂ = 0.4 (moderate progression)
- δ₁ = 0.087 (to ICU)
- δ₂ = 0.1 (to recovery from hospital)
- ρ = 0.048 (post-ICU recovery)
- μ = 0.0095 (death from ICU)
- p_s = 0.03 (symptom development)

All flows should include these where applicable. Use comments if a rate is uncertain.

"""

covid_image_minimal = """
0. Susceptible
1. Exposed
2. Exposed Quarantined
3. Infectious Presymptomatic
4. Infectious Presymptomatic, Isolated
5. Infectious Mild/Moderate, Isolated
6. Infectious Mild/Moderate
7. Infectious Severe
8. Infectious Severe, Isolated
9. Isolated
10. Admitted to Hospital
11. Admitted to Hospital Pre-ICU
12. ICU
13. Admitted to Hospital Post-ICU
14. Death
15. Recovered
"""

LANG_SPECS_FILENAME = "seirmodel_skeleton.txt"
OUTPUT_SEIRMODEL_FILENAME = "seir_model.txt"

#generate_seirmodel(PROMPT_ONLY_TEXT, simplified_hiv_user_input, LANG_SPECS_FILENAME, "hiv.txt")
#generate_seirmodel(PROMPT_ONLY_TEXT, covid_user_input, LANG_SPECS_FILENAME, "covid.txt")
generate_seirmodel_from_image(PROMPT_WITH_IMAGE, "covidModel(epimde).jpg", covid_image_minimal, LANG_SPECS_FILENAME, "covid_with_image.txt")