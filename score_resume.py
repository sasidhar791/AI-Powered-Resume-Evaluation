from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from typing import List
import pypdf
import docx
import io
import pandas as pd
import google.generativeai as genai
import json

# Initialize FastAPI app
app = FastAPI()

# Set your Google Gemini API key
GOOGLE_GEMINI_API_KEY = "add_your_google_gemini_api_key_here"
genai.configure(api_key=GOOGLE_GEMINI_API_KEY)

# Function to extract text from PDF
def extract_text_from_pdf(file):
    reader = pypdf.PdfReader(file)
    text = "\n".join([page.extract_text() or "" for page in reader.pages])
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = docx.Document(io.BytesIO(file))
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# Function to send criteria & resume text to LLM for scoring
def score_resume_with_llm(resume_text, criteria):
    prompt = f"""
    You are an AI resume evaluator. Given the following resume and ranking criteria, assign a score (0-5) for each criterion.

    **Ranking Criteria:** {criteria}

    **Resume:** {resume_text}

    Return the results in the following structured JSON format:
    {{
      "scores": {{
        "Criterion 1": score (0-5),
        "Criterion 2": score (0-5),
        ...
      }},
      "total_score": total (sum of all criterion scores)
    }}
    """

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    result = response.text.strip()

    # Convert response to dictionary (Ensure it's valid JSON)
    try:
        scores = json.loads(result)
    except json.JSONDecodeError:
        print("Invalid LLM response:", result)
        return None  # Handle errors gracefully

    return scores

# API Endpoint to process resumes and score them
@app.post("/score-resumes")
async def score_resumes(
    criteria: List[str] = Form(...),  # Accepts multiple ranking criteria
    files: List[UploadFile] = File(...)  # Accepts multiple resume files
):
    results = []

    for file in files:
        # Extract text from each resume
        if file.filename.endswith(".pdf"):
            resume_text = extract_text_from_pdf(file.file)
        elif file.filename.endswith(".docx"):
            resume_text = extract_text_from_docx(file.file.read())
        else:
            continue  # Skip unsupported files

        # Get scores from LLM
        llm_result = score_resume_with_llm(resume_text, criteria)

        if not llm_result or "scores" not in llm_result:
            continue  # Skip if LLM fails

        # Extract candidate name (assuming filename represents name)
        candidate_name = file.filename.replace(".pdf", "").replace(".docx", "")

        # Store result
        results.append({
            "Candidate Name": candidate_name,
            **llm_result["scores"],
            "Total Score": llm_result["total_score"]
        })

    # Convert results to a DataFrame
    df = pd.DataFrame(results)

    # Save as Excel file
    output_file = "scored_resumes.xlsx"
    df.to_excel(output_file, index=False)

    # Return the file for download
    return FileResponse(output_file, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=output_file)
