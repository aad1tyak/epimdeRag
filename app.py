import fitz
import os
import re
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import cohere
import ast
import xml.etree.ElementTree as ET

#initialize cohere client
co = cohere.Client("COHERE_API_KEY")  # Replace with your actual API key


def load_pdf(names) -> str:
    """
    Load a PDF file and return its content as a string.

    Args:
        names (list): List of PDF file names to load.

    Returns:
        str: The combined text content of the PDF files, or None if an error occurs.
    """
    for file_name in names:
        try:
            with fitz.open(f'papers/{file_name}') as pdf_document: # Open the PDF file
                content = [] 
                for page in pdf_document: # Iterate through each page
                    content.append(page.get_text()) 
                return "\n".join(content) 
        except Exception as e:
            print(f"Error loading PDF: {e}")
            return None
    

def chunk_section(text, max_tokens=250):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current.split()) + len(sentence.split()) < max_tokens:
            current += " " + sentence
        else:
            chunks.append(current.strip())
            current = sentence
    if current.strip():
        chunks.append(current.strip())
    return chunks

def chunk_text(text: str, names: list) -> list:
    """
    Chunks the provided text into uniform blocks for each given name.
    Args:
        text (str): The full text to be chunked.
        names (list): A list of file or section names to associate with the chunks.
    Returns:
        list: A list of dictionaries, each containing a 'name' and its corresponding 'chunks' from the text.
    """

    all_documents = []
    for file_name in names:
        chunks = chunk_section(text)
        all_documents.append({
            "name": file_name,
            "chunks": chunks
        })

    return all_documents


def embed_chunks(chunks: list, model_name="all-MiniLM-L6-v2"):
    """
    Embeds a list of text chunks using a HuggingFace sentence transformer model.

    Args:
        chunks (list): A list of text strings to be embedded.
        model_name (str, optional): The name of the HuggingFace sentence transformer model to use. Defaults to "all-MiniLM-L6-v2".

    Returns:
        numpy.ndarray: An array of embeddings corresponding to the input text chunks.
    """

    model = SentenceTransformer(model_name)
    embeddings = model.encode(chunks, convert_to_numpy=True, show_progress_bar=True)
    return embeddings

def save_to_faiss(embeddings: np.ndarray, metadata: list, index_path: str, meta_path: str):
    """
    Save embeddings to FAISS index
    """
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    faiss.write_index(index, index_path)

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)




def cohere_rerank(question, chunks, model="rerank-v3.5", threshold_score=0.8): 
    """
    Rerank chunks based on relevance to the question using Cohere's reranking model.

    Args:
        question (str): The query/question to rerank against.
        chunks (list): List of text chunks to be reranked.
        model (str, optional): Cohere rerank model name. Defaults to "rerank-v3.5".
        threshold_score (float, optional): Minimum relevance score to include a chunk. Defaults to 0.8.

    Returns:
        list: List of reranked chunks above the threshold, or the top chunk if none meet the threshold.
    """
    response = co.rerank(
        model=model,
        query=question,
        documents=chunks,
        top_n=len(chunks)
    )

    reranked_chunks = []

    # Build a list of (chunk, score) tuples
    scored_chunks = [
        (chunks[result.index], result.relevance_score)
        for result in response.results
    ]

    # Filter by threshold
    for chunk, score in scored_chunks:
        if score >= threshold_score:
            reranked_chunks.append(
                f'NOTE: The following context has Relevance Score of: {score:.2f} (Scores are betwee 0 and 1 with 0 being least and 1 is highest) which has been flagged as High relevancy. You can be confident with using it: \n{chunk}'
            )

    # Fallback if no chunk passes threshold
    if len(reranked_chunks) == 0 and scored_chunks:
        top_chunk, top_score = max(scored_chunks, key=lambda x: x[1])
        reranked_chunks.append(
            f"NOTE: The following context has Relevance Score of: {top_score:.2f} (Scores are betwee 0 and 1 with 0 being least and 1 is highest) which has been flagged as Low relevancy. Use it with Caution, its not compulsory to use every bit of information provided: \n{top_chunk}"
        )

    return reranked_chunks


def generate_questions(prompt: str, user_input: str, langSpecs_path):
    """
    Generate questions based on a prompt, user input, and language specifications using Cohere's generate model.
    Args:
        prompt (str): The initial prompt or instruction to guide question generation.
        user_input (str): Additional user-provided input to contextualize the questions.
        langSpecs_path (str): File path to the language specifications file.
    Returns:
        list: A list of generated questions if successful, or a list containing an error message if extraction fails.
    """
    with open(langSpecs_path, "r", encoding="utf-8") as f:
        lang_specs = f.read()
    
    
    final_prompt = f'prompt: {prompt}\n\nuser_input: {user_input}\n\nlang_specs: {lang_specs}'

    response = co.chat(
    model="command-a-03-2025",
    messages=[{"role": "user", "content": final_prompt}],
    )   
    try:
        content_blocks = response.get("message", {}).get("content", [])
        if not content_blocks or not isinstance(content_blocks, list):
            return ["Issue: response content is missing or not a list."]

        text = content_blocks[0].get("text", "").strip()

        if text.startswith("```"):
            text = text.strip("`")  
            lines = text.splitlines()
            if lines and lines[0].startswith("python"):
                lines = lines[1:]  
            text = "\n".join(lines)

        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return parsed
        else:
            return ["Issue: response content was not a valid list."]
    except Exception as e:
        return [f"Issue: Failed to extract list from response. Error: {str(e)}"]
    






def search_questions_in_vector_db(questions, index_path, metadata_path, model_name="all-MiniLM-L6-v2", top_k=10):
    """
    Given a list of questions, run vector search on each and return top-k contexts with sources.

    Args:
        questions (list): List of question strings to search for.
        index_path (str): Path to the FAISS index file.
        metadata_path (str): Path to the metadata JSON file.
        model_name (str, optional): Name of the embedding model. Defaults to "all-MiniLM-L6-v2".
        top_k (int, optional): Number of top results to return per question. Defaults to 10.

    Returns:
        list: List of dicts like:
            [
                {
                    "q": "your question",
                    "context": [
                        {"source_name.pdf": "matching chunk"},
                        ...
                    ]
                },
                ...
            ]
    """
    # Load index and metadata
    index = faiss.read_index(index_path)
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Load embedding model
    model = SentenceTransformer(model_name)

    results = []

    for question in questions:
        q_embedding = model.encode([question], convert_to_numpy=True)

        # Search vector index
        _, indices = index.search(q_embedding, top_k)


        top_contexts = []
        for i in indices[0]:
            if i < len(metadata):
                entry = metadata[i]
                top_contexts.append({entry["source"]: entry["text"]})

        # Rerank using Cohere
        reranked_contexts = cohere_rerank(
            question,
            [list(c.values())[0] for c in top_contexts]
        )

        results.append({
            "q": question,
            "context": reranked_contexts
        })

    return results



def generate_seirmodel_xml(prompt: str, user_input: str, langSpecs_path: str, context: str, output_path: str) -> str:
    """
    Generate SEIR model XML content using Cohere and save to output_path.

    Parameters:
        prompt (str): The system prompt guiding XML generation.
        user_input (str): User-provided compartment and parameter data.
        langSpecs_path (str): Path to the SEIR language specification file.
        context (str): Answered context from RAG.
        output_path (str): Path where final XML file will be written.

    Returns:
        str: Success message or error details.
    """


    try:
        with open(langSpecs_path, "r", encoding="utf-8") as f:
            lang_specs = f.read()

        # Build the final string prompt (as Cohere expects a single string input)
        final_prompt = f'prompt: {prompt}\n\nuser_input: {user_input}\n\nlang_specs: {lang_specs}\n\ncontext: {context}'

        response = co.chat(
            model="command-a-03-2025",
            messages=[{"role": "user", "content": final_prompt}]
        )

        content_blocks = response.get("message", {}).get("content", [])
        if not content_blocks or not isinstance(content_blocks, list):
            return "Issue: Response content is missing or not a list."

        text = content_blocks[0].get("text", "").strip()

        # Remove markdown formatting if present
        if text.startswith("```"):
            text = text.strip("`")
            lines = text.splitlines()
            if lines and lines[0].lower().strip().startswith("xml"):
                lines = lines[1:]
            text = "\n".join(lines)

        # XML Structural Validation
        try:
            ET.fromstring(text)
        except ET.ParseError as e:
            return f"Issue: XML validation failed. Error: {str(e)}"

        # Write to file if valid
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        return f"SEIR model successfully written to {output_path}"

    except Exception as e:
        return f"Issue: Failed to generate or save SEIR model. Error: {str(e)}"

 





#MAIN EXECUTION BLOCK

#Global Constants
FILE_NAMES = ["Mathematical_Model_of_HIV.pdf"] 
METADATA_FILENAME = "metadata.json"
VECTOR_FILENAME =  "index.faiss"
LANG_SPECS_FILENAME = "seirmodel_skeleton.txt"
OUTPUT_SEIRMODEL_FILENAME = "seir_model.seirmodel"

USER_INPUT = ""

QUERY_RETRIVAL_PROMPT = """
Your task is to generate a list of specific and useful questions that will later be answered by searching through a large collection of research papers. 
You are part of a Retrieval-Augmented Generation (RAG) system, and your role is to identify missing information in the user_input that would help accurately complete a full SEIR model file. 
Use the seirmodel_skeleton as a guide to understand what information is expected. 
1. A user-specified list of compartments and parameter information (called `user_input`).
2. A sample XML SEIR model skeleton in TXT format (called `lang_specs`).


Be mindful:
- DO NOT modify or suggest edits to the `seirmodel_skeleton`. It is shown only for structure reference.
- Ask only "targeted questions" that, when answered, would help you build a correct and complete SEIR model in XML.
- Be specific, but do not overfit — ask practical modeling questions that a modeler would typically clarify.
- Do not ask extremely generic or overly specific scientific questions unless clearly required by the `user_input`.
- "Only include clean, logically phrased questions. No duplicates. No filler. No clarifications about your role."

FORMATE RULES (VERY IMPORTANT):
- Output must be a "valid Python list of strings". Like this:

```python
["Question 1 here", "Question 2 here", "Question 3 here", ...]
```
-DO NOT return anything outside the list. No formatting, headers, explanations, or metadata.
-DO NOT include any malformed, blank, or placeholder strings.

You are expected to think like an expert modeler — precise, minimal, informative, and useful.
Now generate the list of questions.
"""

SEIRMODEL_GENERATION_PROMPT = """
You are now responsible for generating a complete SEIR model XML file using the provided information. You are part of a structured RAG-based system that has already retrieved the relevant context and answered key questions to support this generation.

You have access to:

-user_input: The initial description of compartments, flows, and assumptions provided by the user.
-language_specification: A skeleton XML file that defines the required structure, rules, and formatting. Do not alter any of the structural lines marked as required.
-context: A set of answers retrieved from research papers that help fill in missing or detailed information without hallucinations.

Your output must be:

1. A complete and valid XML file that follows the structure and formatting of the seirmodel_skeleton.

2. Contain all compartments and flows necessary to reflect the user's input and the supporting context from the answers.

3. Only the XML — no explanation, notes, or formatting outside the XML.

4. If a value is not known or still unclear, leave it as a clear placeholder with a comment explaining what’s missing (e.g., rate="UNKNOWN" <!-- unclear flow rate -->).

5. Preserve any required lines exactly as shown in the skeleton — especially the first two and last line.

Be accurate, be strict, and keep it clean. This output will be directly parsed by downstream systems.
"""


chunked_docs = chunk_text(load_pdf(FILE_NAMES), FILE_NAMES)

all_chunks = []
metadata = []
for doc in chunked_docs:
    for chunk in doc["chunks"]:
        all_chunks.append(chunk)
        metadata.append({"text": chunk, "source": doc["name"]})

embeddings = embed_chunks(all_chunks)
save_to_faiss(embeddings, metadata, VECTOR_FILENAME, METADATA_FILENAME)

questions = generate_questions(QUERY_RETRIVAL_PROMPT, USER_INPUT, LANG_SPECS_FILENAME)

answers = search_questions_in_vector_db(questions, VECTOR_FILENAME, METADATA_FILENAME)

result = generate_seirmodel_xml(SEIRMODEL_GENERATION_PROMPT, USER_INPUT, LANG_SPECS_FILENAME, answers, OUTPUT_SEIRMODEL_FILENAME)

print(result) 
