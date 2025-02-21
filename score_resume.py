from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from typing import List
import pypdf
import docx
import io
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema

# Initialize FastAPI app
app = FastAPI()

GOOGLE_GEMINI_API_KEY = "add_your_google_gemini_api_key_here"
llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_GEMINI_API_KEY)


response_schemas = [
ResponseSchema(name="criteria_scores", description="A dictionary where keys are criteria names and values are scores (0-5)."),
ResponseSchema(name="total_score", description="The sum of all individual criteria scores.")    
]

# Create the output parser
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = output_parser.get_format_instructions()


# Function to extract text from PDF
def extract_text_from_pdf(file):
    reader = pypdf.PdfReader(file)
    return "\n".join([page.extract_text() or "" for page in reader.pages])
    

# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = docx.Document(io.BytesIO(file))
    return "\n".join([para.text for para in doc.paragraphs])    


# Function to send criteria & resume text to LLM for scoring
def score_resume_with_llm(resume_text, criteria):

    criteria = ", ".join(criteria)  

    prompt_template = PromptTemplate(  
    input_variables=["criteria", "resume_text", "format_instructions"],  
    template="""
    You are an AI resume evaluator. Given the following resume and ranking criteria, assign a score (0-5) for each criterion.

    Ranking Criteria: {criteria}

    Resume: {resume_text}

    Return the output strictly in the following JSON format:
    {format_instructions}
    
    """
    )

    # Ensure that "total_score" is the sum of all individual scores from "criteria_scores".
    llm_chain = LLMChain(llm = llm,prompt = prompt_template)
    llm_response = llm_chain.run(resume_text=resume_text,criteria=criteria,format_instructions=format_instructions)
    
    try:
        # Convert response to structured JSON
        parsed_output = output_parser.parse(llm_response)
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        return None

    return parsed_output




def process_resume(file, criteria):
    """Extract text and get scores from LLM."""
    try:
        if file.filename.endswith(".pdf"):
            resume_text = extract_text_from_pdf(file.file)
        elif file.filename.endswith(".docx"):
            resume_text = extract_text_from_docx(file.file.read())
        else:
            return None  # Skip unsupported files

        # Get scores from LLM
        llm_result = score_resume_with_llm(resume_text, criteria)

        if not llm_result or "criteria_scores" not in llm_result or "total_score" not in llm_result:        
            return None  # Skip if LLM fails

        # Extract candidate name
        candidate_name = file.filename.replace(".pdf", "").replace(".docx", "")

        return {
            "Candidate Name": candidate_name,
            **llm_result["criteria_scores"],
            "Total Score": llm_result["total_score"]
        }
    except Exception as e:
        return {"error": f"Processing failed for {file.filename}: {str(e)}"}

@app.post("/score-resumes")
async def process_all_resumes(criteria: List[str] = Form(...),  # Accepts multiple ranking criteria
    files: List[UploadFile] = File(...)):
    # Convert files to a DataFrame
    df = pd.DataFrame({"file": files})

    # Apply function to process resumes
    df["processed_data"] = df["file"].apply(lambda file: process_resume(file, criteria))

    # Filter out failed cases
    df = df.dropna(subset=["processed_data"])

    # Expand dictionary columns
    df = pd.json_normalize(df["processed_data"])

    # Save as Excel file
    output_file = "scored_resumes.xlsx"
    df.to_excel(output_file, index=False)

    # Return the file
    return FileResponse(output_file, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=output_file)
